from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth import router as auth_router
from app.config import settings
from app.database import engine
from app.dashboard import router as dashboard_router
from app.quiz import router as quiz_router
from app.study import router as study_router
from app.vocabularies import router as vocabulary_router

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
trusted_origins = {origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()}


@app.middleware("http")
async def enforce_trusted_origin(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin not in trusted_origins:
            return JSONResponse(status_code=403, content={"detail": "Untrusted request origin"})
    return await call_next(request)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(vocabulary_router)
app.include_router(study_router)
app.include_router(quiz_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/database", tags=["health"])
def database_health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database unavailable") from None

    return {"status": "ok"}