from fastapi import FastAPI
from app.config import settings


app = FastAPI(
    title="Bourhan Teacher AI",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "project": "Bourhan Teacher AI",
        "status": "running 🚀",
        "environment": settings.environment
    }
