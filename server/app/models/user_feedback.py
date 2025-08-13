from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_hash = Column(String, nullable=False)  # Hash of query+response for uniqueness
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True) 
    vote = Column(Integer, nullable=False)  # 1 for like, -1 for dislike
    query = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    conversation = relationship("Conversation", back_populates="feedback")
    
    # Ensure one feedback per user per message
    __table_args__ = (
        UniqueConstraint('user_id', 'message_hash', name='unique_user_message_feedback'),
    )