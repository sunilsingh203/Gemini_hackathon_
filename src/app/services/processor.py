import time
import logging
from sqlalchemy.orm import Session
from app.models.resume import Resume

logger = logging.getLogger(__name__)

def process_resume_background(db: Session, resume_id: str):
    """Simulate parsing the resume after a short delay."""
    logger.info(f"Started fake processing for resume {resume_id}")
    time.sleep(5)  # simulate ML/NLP work taking time
    
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        logger.warning(f"Resume {resume_id} not found during processing")
        return
    
    resume.processing_status = "completed"
    resume.raw_text = "This is simulated extracted text from the resume."
    resume.structured_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "FastAPI", "SQLAlchemy"],
        "experience_years": 3
    }
    db.commit()
    logger.info(f"Completed fake processing for resume {resume_id}")
