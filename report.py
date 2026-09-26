"""Report data aggregation.

SQL used by get_report_data():

    -- total_orders
    SELECT COUNT(*) AS total_orders FROM orders;

    -- total_revenue
    SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS total_revenue FROM orders;

    -- top_5_products
    SELECT product,
           COUNT(*)              AS orders,
           ROUND(SUM(amount), 2) AS revenue
    FROM orders
    GROUP BY product
    ORDER BY revenue DESC
    LIMIT 5;

    -- orders_per_day_7days (today and the 6 days before it)
    SELECT created_at            AS day,
           COUNT(*)              AS orders,
           ROUND(SUM(amount), 2) AS revenue
    FROM orders
    WHERE created_at >= DATE('now', 'localtime', '-6 days')
    GROUP BY created_at
    ORDER BY created_at;
"""
import json
from datetime import date, timedelta

from db import get_conn

TOTAL_ORDERS_SQL = "SELECT COUNT(*) AS total_orders FROM orders"
TOTAL_REVENUE_SQL = "SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS total_revenue FROM orders"
TOP_PRODUCTS_SQL = """
    SELECT product, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
    FROM orders
    GROUP BY product
    ORDER BY revenue DESC
    LIMIT 5
"""
ORDERS_PER_DAY_SQL = """
    SELECT created_at AS day, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
    FROM orders
    WHERE created_at >= DATE('now', 'localtime', '-6 days')
    GROUP BY created_at
    ORDER BY created_at
"""


def get_report_data() -> dict:
    conn = get_conn()
    try:
        total_orders = conn.execute(TOTAL_ORDERS_SQL).fetchone()[0]
        total_revenue = conn.execute(TOTAL_REVENUE_SQL).fetchone()[0]
        top_5 = [dict(r) for r in conn.execute(TOP_PRODUCTS_SQL)]
        by_day = {r["day"]: dict(r) for r in conn.execute(ORDERS_PER_DAY_SQL)}
    finally:
        conn.close()

    # Fill days with no orders so the series always has 7 entries.
    today = date.today()
    per_day = []
    for offset in range(6, -1, -1):
        d = (today - timedelta(days=offset)).isoformat()
        per_day.append(by_day.get(d, {"day": d, "orders": 0, "revenue": 0.0}))

    return {
        "generated_at": today.isoformat(),
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_5_products": top_5,
        "orders_per_day_7days": per_day,
    }


# Alias matching the spec's naming.
getReportData = get_report_data


if __name__ == "__main__":
    print(json.dumps(get_report_data(), indent=2))
