from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from db import get_conn, init_db
from pdf import REPORTS_DIR, render_pdf
from report import get_report_data

BASE_DIR = Path(__file__).parent



@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_conn()
    init_db(conn)
    conn.close()
    REPORTS_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(title="FlyRank A8 - PDF Report Generator", lifespan=lifespan)


def _file_link(report_id: int) -> str:
    return f"/reports/{report_id}/file"


def _get_report_row(report_id: int) -> dict:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, path, created_at FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="report not found")
    return dict(row)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reports", status_code=201)
def create_report():
    conn = get_conn()
    pdf_path = None
    try:
        conn.execute("BEGIN IMMEDIATE")
        report_id = conn.execute(
            "INSERT INTO reports (path, created_at) VALUES (NULL, ?)",
            (date.today().isoformat(),),
        ).lastrowid
        rel_path = f"reports/{report_id}.pdf"
        pdf_path = BASE_DIR / rel_path
        render_pdf(get_report_data(), pdf_path)
        conn.execute("UPDATE reports SET path = ? WHERE id = ?", (rel_path, report_id))
        conn.commit()
    except Exception:
        conn.rollback()
        if pdf_path is not None:
            pdf_path.unlink(missing_ok=True)
        raise
    finally:
        conn.close()
    return JSONResponse(status_code=201, content={"id": report_id, "file": _file_link(report_id)})


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    # Metadata only -- the PDF bytes are served by /reports/{id}/file.
    row = _get_report_row(report_id)
    return {**row, "file": _file_link(report_id)}


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    row = _get_report_row(report_id)
    pdf_path = BASE_DIR / row["path"] if row["path"] else None
    if pdf_path is None or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="report file missing")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"report-{report_id}.pdf")
