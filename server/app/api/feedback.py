from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.services.feedback_service import feedback_service
from app.services.rag_service import RAGService
from app.crud import crud_document
from app.models.user_feedback import UserFeedback
from app.models.user import User
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import hashlib
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class FeedbackRequest(BaseModel):
    query: str
    vote: int  # 1 for like, -1 for dislike
    source_documents: List[Dict[str, Any]]
    response_text: str
    conversation_id: Optional[int] = None

router = APIRouter()

@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    rag_service: RAGService = Depends(deps.get_rag_service),
):
    """Submit feedback for a RAG response. Prevents duplicate feedback per user per message."""
    
    # Create unique hash for this query+response pair
    message_content = f"{feedback.query}||{feedback.response_text}"
    message_hash = hashlib.md5(message_content.encode('utf-8')).hexdigest()
    
    # Check if user already gave feedback for this message
    existing_feedback = db.query(UserFeedback).filter(
        UserFeedback.user_id == current_user.id,
        UserFeedback.message_hash == message_hash
    ).first()
    
    if existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already provided feedback for this message"
        )
    
    # Validate vote
    if feedback.vote not in [1, -1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vote must be 1 (like) or -1 (dislike)"
        )
    
    # Store user feedback record
    user_feedback = UserFeedback(
        user_id=current_user.id,
        message_hash=message_hash,
        conversation_id=feedback.conversation_id,
        vote=feedback.vote,
        query=feedback.query
    )
    db.add(user_feedback)
    
    # Process document quality scoring (existing logic)
    try:
        score_updates = feedback_service.get_feedback_distribution(
            feedback=feedback.vote,
            source_chunks=feedback.source_documents,
            query=feedback.query,
            rag_service=rag_service
        )
        
        if score_updates:
            crud_document.update_chunk_feedback_scores(db, score_updates=score_updates)
            
    except Exception as e:
        # Don't fail the entire request if document scoring fails
        logger.warning(f"Document scoring failed: {e}")
    
    db.commit()
    return


@router.get("/conversation/{conversation_id}")
def get_conversation_feedback(
    conversation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get all feedback given by the user for messages in a conversation."""
    feedback_list = db.query(UserFeedback).filter(
        UserFeedback.user_id == current_user.id,
        UserFeedback.conversation_id == conversation_id
    ).all()
    
    # Return as dictionary for easy lookup by message hash
    feedback_map = {
        feedback.message_hash: {
            "vote": feedback.vote,
            "created_at": feedback.created_at.isoformat(),
        }
        for feedback in feedback_list
    }
    
    return {"feedback": feedback_map}


@router.get("/check")
def check_feedback_exists(
    query: str,
    response_text: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Check if user has already given feedback for a specific query+response pair."""
    message_content = f"{query}||{response_text}"
    message_hash = hashlib.md5(message_content.encode('utf-8')).hexdigest()
    
    existing_feedback = db.query(UserFeedback).filter(
        UserFeedback.user_id == current_user.id,
        UserFeedback.message_hash == message_hash
    ).first()
    
    if existing_feedback:
        return {
            "has_feedback": True,
            "vote": existing_feedback.vote,
            "created_at": existing_feedback.created_at.isoformat()
        }
    
    return {"has_feedback": False}