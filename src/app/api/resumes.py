from typing import Optional
from json import loads as json_loads, JSONDecodeError

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    Depends,
    HTTPException,
    BackgroundTasks,
    Path,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.resume import Resume
from app.schemas.resume import UploadResponse, UploadOptions
from app.utils.files import validate_file, read_and_hash, save_bytes
from app.services.processor import process_resume_background

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/resumes/upload", response_model=UploadResponse, tags=["Resumes"])
async def upload_resume(
    background_tasks: BackgroundTasks,  # trigger background processing
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),  # JSON as string (optional)
    webhookUrl: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # 1) Validate type/extension
    validate_file(file)

    # 2) Parse options JSON (if provided)
    parsed_options = UploadOptions()
    if options:
        try:
            parsed_options = UploadOptions(**json_loads(options))
        except JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in 'options' field")

    # 3) Read file into memory, enforce size, compute hash
    data, sha256hex, size_bytes = read_and_hash(file, settings.MAX_FILE_SIZE_MB)

    # 4) Save bytes to disk
    saved_path = save_bytes(data, file.filename or "upload.bin")

    # 5) Check for duplicate by hash (idempotent-ish)
    existing = db.query(Resume).filter(Resume.file_hash == sha256hex).first()
    if existing:
        return UploadResponse(
            id=existing.id,
            status=existing.processing_status or "processing",
            message="Resume already exists (by hash). Reusing existing record.",
            estimatedProcessingTime=30,
            webhookUrl=webhookUrl,
        )

    # 6) Create DB row
    resume = Resume(
        file_name=file.filename or "unknown",
        file_size=size_bytes,
        file_type=file.content_type or "application/octet-stream",
        file_hash=sha256hex,
        processing_status="processing",
        structured_data=None,
        raw_text=None,
        ai_enhancements=None,
        meta={
            "path": saved_path,
            "webhookUrl": webhookUrl,
            "options": parsed_options.model_dump(),
        },
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 7) Kick off background processing
    background_tasks.add_task(process_resume_background, db, resume.id)

    # 8) Return immediate processing response
    return UploadResponse(
        id=resume.id,
        status="processing",
        message="Resume uploaded successfully",
        estimatedProcessingTime=30,
        webhookUrl=webhookUrl,
    )


@router.get("/resumes/{id}", tags=["Resumes"])
def get_resume(id: str = Path(...), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {
        "id": resume.id,
        "status": resume.processing_status,
        "file_name": resume.file_name,
        "raw_text": resume.raw_text,
        "structured_data": resume.structured_data,
        "ai_enhancements": resume.ai_enhancements,
    }


@router.get("/resumes/{id}/status", tags=["Resumes"])
def get_resume_status(id: str = Path(...), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {
        "id": resume.id,
        "status": resume.processing_status,
    }
