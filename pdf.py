"""Render report data to a PDF via headless Chromium (Playwright)."""
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

from db import get_conn

REPORTS_DIR = Path(__file__).parent / "reports"

CSS = """
@page { size: A4; margin: 18mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Helvetica, Arial, sans-serif; color: #1f2933; font-size: 11px; margin: 0; }
h1 { font-size: 22px; margin: 0 0 2px; }
h2 { font-size: 14px; margin: 22px 0 8px; border-bottom: 2px solid #3b5bdb; padding-bottom: 4px; }
.date { color: #616e7c; margin-bottom: 16px; }
.totals { display: flex; gap: 12px; }
.card { flex: 1; background: #edf2ff; border-radius: 6px; padding: 10px 14px; }
.card .label { color: #616e7c; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; }
.card .value { font-size: 20px; font-weight: 600; margin-top: 2px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 5px 8px; text-align: left; border-bottom: 1px solid #e4e7eb; }
th { background: #3b5bdb; color: #fff; font-weight: 600; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tbody tr:nth-child(even) td { background: #f5f7fa; }
/* Clean page breaks: never slice a row, repeat the header on each page. */
tr { break-inside: avoid; page-break-inside: avoid; }
thead { display: table-header-group; }
h2 { break-after: avoid; }
"""


def _money(v: float) -> str:
    return f"${v:,.2f}"


def get_all_orders() -> list[dict]:
    conn = get_conn()
    try:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT id, customer, product, amount, created_at FROM orders "
                "ORDER BY created_at DESC, id"
            )
        ]
    finally:
        conn.close()


def build_html(report_data: dict, orders: list[dict]) -> str:
    top_rows = "".join(
        f"<tr><td>{i}</td><td>{escape(p['product'])}</td>"
        f"<td class='num'>{p['orders']}</td><td class='num'>{_money(p['revenue'])}</td></tr>"
        for i, p in enumerate(report_data["top_5_products"], 1)
    )
    day_rows = "".join(
        f"<tr><td>{d['day']}</td><td class='num'>{d['orders']}</td>"
        f"<td class='num'>{_money(d['revenue'])}</td></tr>"
        for d in report_data["orders_per_day_7days"]
    )
    order_rows = "".join(
        f"<tr><td class='num'>{o['id']}</td><td>{o['created_at']}</td>"
        f"<td>{escape(o['customer'])}</td><td>{escape(o['product'])}</td>"
        f"<td class='num'>{_money(o['amount'])}</td></tr>"
        for o in orders
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Orders Report</title><style>{CSS}</style></head>
<body>
  <h1>Orders Report</h1>
  <div class="date">Generated {escape(report_data["generated_at"])}</div>

  <div class="totals">
    <div class="card"><div class="label">Total orders</div><div class="value">{report_data["total_orders"]}</div></div>
    <div class="card"><div class="label">Total revenue</div><div class="value">{_money(report_data["total_revenue"])}</div></div>
  </div>

  <h2>Top 5 products by revenue</h2>
  <table>
    <thead><tr><th>#</th><th>Product</th><th class="num">Orders</th><th class="num">Revenue</th></tr></thead>
    <tbody>{top_rows}</tbody>
  </table>

  <h2>Orders per day (last 7 days)</h2>
  <table>
    <thead><tr><th>Day</th><th class="num">Orders</th><th class="num">Revenue</th></tr></thead>
    <tbody>{day_rows}</tbody>
  </table>

  <h2>All orders ({len(orders)})</h2>
  <table>
    <thead><tr><th class="num">ID</th><th>Date</th><th>Customer</th><th>Product</th><th class="num">Amount</th></tr></thead>
    <tbody>{order_rows}</tbody>
  </table>
</body></html>"""


def render_pdf(report_data: dict, path: str | Path = REPORTS_DIR / "test.pdf") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = build_html(report_data, get_all_orders())
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            page.pdf(path=str(path), format="A4", print_background=True)
        finally:
            browser.close()
    return path


# Alias matching the spec's naming.
renderPDF = render_pdf


if __name__ == "__main__":
    from report import get_report_data

    out = render_pdf(get_report_data())
    print(f"wrote {out} ({out.stat().st_size} bytes)")
