from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import is_database_available
from app.routers import analytics, predict

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Credit Risk API",
    description="Predicts probability of default, credit rating, and expected loss for a borrower.",
    version="2.0.0",
)

app.include_router(predict.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    """The usable dashboard lives here — this is what you open in a browser."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "healthy", "database_connected": is_database_available()}
