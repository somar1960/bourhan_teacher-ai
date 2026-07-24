from fastapi import FastAPI
from app.config import settings


app = FastAPI(
    title="Bourhan Teacher AI",
    description="AI Educational Platform for Teachers and Students",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "project": "Bourhan Teacher AI",
        "message": "Platform is running 🚀",
        "environment": settings.environment,
        "timezone": settings.timezone
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Bourhan Teacher AI"
    }
