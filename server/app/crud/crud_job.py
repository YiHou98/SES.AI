from sqlalchemy.orm import Session
from app.models.job import Job

def create_job(db: Session, job_id: str, user_id: int) -> Job:
    db_job = Job(id=job_id, user_id=user_id, status="pending", details="Upload accepted, pending processing.")
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_job(db: Session, job_id: str) -> Job | None:
    return db.query(Job).filter(Job.id == job_id).first()

def update_job_status(db: Session, job_id: str, status: str, details: str) -> Job | None:
    db_job = get_job(db, job_id)
    if db_job:
        db_job.status = status
        db_job.details = details
        db.commit()
        db.refresh(db_job)
    return db_job