from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from json import loads as json_loads, JSONDecodeError

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.resume import Resume
from app.schemas.resume import UploadResponse, UploadOptions
from app.utils.files import validate_file, read_and_hash, save_bytes

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/resumes/upload", response_model=UploadResponse, tags=["Resumes"])
async def upload_resume(
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),  # JSON as string in multipart; optional
    webhookUrl: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # 1) Validate type
    validate_file(file)

    # 2) Parse options
    parsed_options = UploadOptions()
    if options:
        try:
            parsed_options = UploadOptions(**json_loads(options))
        except JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in 'options' field")

    # 3) Read bytes + hash + size
    data, sha256hex, size_bytes = read_and_hash(file, settings.MAX_FILE_SIZE_MB)

    # 4) Persist file
    saved_path = save_bytes(data, file.filename or "upload.bin")

    # 5) Create DB row
    resume = Resume(
        file_name=file.filename or "unknown",
        file_size=size_bytes,
        file_type=file.content_type or "application/octet-stream",
        file_hash=sha256hex,
        processing_status="processing",
        meta={
            "path": saved_path,
            "webhookUrl": webhookUrl,
            "options": parsed_options.model_dump(),
        },
        structured_data=None,
        raw_text=None,
        ai_enhancements=None,
    )

    # Avoid duplicate by hash (idempotent-ish). If exists, return existing id.
    existing = db.query(Resume).filter(Resume.file_hash == sha256hex).first()
    if existing:
        # You could also decide to create a new attempt; for now, reuse
        return UploadResponse(
            id=existing.id,
            status=existing.processing_status or "processing",
            message="Resume already exists (by hash). Reusing existing record.",
            estimatedProcessingTime=30,
            webhookUrl=webhookUrl,
        )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    # 6) Return stubbed processing response
    return UploadResponse(
        id=resume.id,
        status="processing",
        message="Resume uploaded successfully",
        estimatedProcessingTime=30,
        webhookUrl=webhookUrl,
    )
