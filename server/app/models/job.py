from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base_class import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")
    details = Column(String, nullable=True)