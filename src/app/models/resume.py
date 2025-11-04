import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_hash = Column(String(128), unique=True, nullable=True)

    uploaded_at = Column(DateTime, server_default=func.current_timestamp())
    processed_at = Column(DateTime, nullable=True)
    processing_status = Column(String(50), default="pending")

    raw_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    ai_enhancements = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships (we’ll create tables later; keeping simple for Step 1)
    # person_info = relationship("PersonInfo", back_populates="resume", cascade="all, delete-orphan")
