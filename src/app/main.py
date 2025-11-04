from fastapi import FastAPI
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.health import router as health_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# Routers
app.include_router(health_router, prefix=settings.API_V1_PREFIX)

@app.get("/", tags=["Root"])
def root():
    return {"message": "AI Resume Parser backend is up"}
