import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "report.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER,
            customer TEXT,
            product TEXT,
            amount REAL,
            created_at DATE
        )
        """
    )
    conn.commit()
