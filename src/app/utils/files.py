import hashlib
import os
import time
from typing import Tuple
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings

ALLOWED_EXTS = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc
    "text/plain",
    "image/png",
    "image/jpeg",
}

UPLOAD_DIR = Path("storage") / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _ext(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]

def validate_file(file: UploadFile):
    ext = _ext(file.filename or "")
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    # Content-Type is client-provided; keep soft check only
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        # allow unknown/blank types; only hard-reject clearly wrong ones
        pass

def read_and_hash(file: UploadFile, max_mb: int) -> Tuple[bytes, str, int]:
    """
    Read the whole file into memory (OK for <=10MB), return (bytes, sha256hex, size_bytes)
    """
    data = file.file.read()
    size_bytes = len(data)
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {max_mb} MB")
    sha256 = hashlib.sha256(data).hexdigest()
    return data, sha256, size_bytes

def save_bytes(data: bytes, original_name: str) -> str:
    """
    Save to storage/uploads/{timestamp}_{original_name_safe}
    Returns relative path string.
    """
    safe_name = original_name.replace("/", "_").replace("\\", "_")
    ts = int(time.time() * 1000)
    out_name = f"{ts}_{safe_name}"
    out_path = UPLOAD_DIR / out_name
    with open(out_path, "wb") as f:
        f.write(data)
    return str(out_path)
