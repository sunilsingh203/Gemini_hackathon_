from pydantic import BaseModel, Field
from typing import Optional

class UploadOptions(BaseModel):
    extractTechnologies: bool = True
    performOCR: bool = True
    enhanceWithAI: bool = True
    anonymize: bool = False
    language: str = "en"

class UploadResponse(BaseModel):
    id: str
    status: str = Field(default="processing")
    message: str = Field(default="Resume uploaded successfully")
    estimatedProcessingTime: int = Field(default=30)  # seconds (stub)
    webhookUrl: Optional[str] = None
