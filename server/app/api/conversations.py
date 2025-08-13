from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models.user import User
from app.schemas.conversation import ConversationInDB
from app.crud import crud_conversation, crud_workspace

router = APIRouter()

@router.get("", response_model=List[ConversationInDB])
def read_conversations(
    workspace_id: int,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    """
    Retrieve all conversations for a specific workspace owned by the current user.
    """
    # 2. Verify the user owns the workspace
    workspace = crud_workspace.get_workspace(db, workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        
    # 3. Fetch conversations for that specific workspace
    return crud_conversation.get_conversations_by_workspace(db, workspace_id=workspace_id)

@router.get("/{conv_id}", response_model=ConversationInDB)
def read_conversation_details(
    conv_id: int,
    db: Session = Depends(deps.get_db),
    user: User = Depends(deps.get_current_active_user)
):
    conversation = crud_conversation.get_conversation(db, conv_id=conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify ownership via the workspace
    workspace = crud_workspace.get_workspace(db, conversation.workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")
        
    return conversation