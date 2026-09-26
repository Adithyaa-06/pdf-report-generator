from fastapi import FastAPI

app = FastAPI(title="FlyRank A8 - PDF Report Generator")


@app.get("/health")
def health():
    return {"status": "ok"}
