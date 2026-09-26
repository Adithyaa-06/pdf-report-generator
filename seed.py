"""Seed report.db with ~200 random orders. Idempotent: wipes orders first."""
import random
from datetime import date, timedelta

from db import get_conn, init_db

N_ORDERS = 200
PRODUCTS = ["Widget", "Gadget", "Gizmo", "Doohickey", "Sprocket", "Thingamajig"]
CUSTOMERS = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank",
    "Grace", "Heidi", "Ivan", "Judy", "Mallory", "Oscar",
]


def seed() -> int:
    conn = get_conn()
    init_db(conn)
    today = date.today()
    rows = [
        (
            i,
            random.choice(CUSTOMERS),
            random.choice(PRODUCTS),
            round(random.uniform(5, 200), 2),
            (today - timedelta(days=random.randint(0, 29))).isoformat(),
        )
        for i in range(1, N_ORDERS + 1)
    ]
    with conn:  # single transaction: delete + insert
        conn.execute("DELETE FROM orders")
        conn.executemany(
            "INSERT INTO orders (id, customer, product, amount, created_at) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    print(f"orders in report.db: {seed()}")
