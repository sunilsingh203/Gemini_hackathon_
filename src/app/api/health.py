from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text  # 👈 add this
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.db.session import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))  # 👈 wrap with text()
        db_ok = "ok"
    except Exception as e:
        # optional: print(e) or log it for debugging
        db_ok = "error"
    return HealthResponse(status="ok", app=settings.APP_NAME, db=db_ok)
