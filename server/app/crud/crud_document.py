from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from typing import List, Dict, Any

def create_document(db: Session, workspace_id: int, filename: str) -> Document:
    db_document = Document(workspace_id=workspace_id, filename=filename)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def create_document_chunks(db: Session, chunks: List[Dict[str, Any]]):
    db_chunks = [DocumentChunk(**chunk) for chunk in chunks]
    db.bulk_save_objects(db_chunks)
    db.commit()

def update_chunk_feedback_scores(db, score_updates: List[Dict[str, Any]]):
    for update in score_updates:
        chunk_id = update["chunk_id"]
        feedback_score = float(update["feedback_score"])  # Convert to Python float
        
        db.query(DocumentChunk).filter(
            DocumentChunk.chunk_id == chunk_id
        ).update({
            "feedback_score": DocumentChunk.feedback_score + feedback_score
        })
    
    db.commit()