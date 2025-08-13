from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, MessageCreate

def get_conversation(db: Session, conv_id: int) -> Optional[Conversation]:
    """获取单个对话"""
    return db.query(Conversation).filter(Conversation.id == conv_id).first()

def get_conversations_by_workspace(
    db: Session, 
    workspace_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Conversation]:
    """获取工作空间的所有对话"""
    return db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id
    ).offset(skip).limit(limit).all()

def create_conversation(
    db: Session, 
    user_id: int, 
    workspace_id: int = None
) -> Conversation:
    """创建新对话"""
    db_conversation = Conversation(
        owner_id=user_id,
        workspace_id=workspace_id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

def create_message(
    db: Session, 
    conversation: Conversation, 
    query: str, 
    response: str,
    model_used: Optional[str] = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    estimated_cost: float = 0.0,
    response_time_ms: Optional[int] = None
) -> Message:
    """
    创建消息记录（包含成本信息）
    """
    # 创建消息
    db_message = Message(
        conversation_id=conversation.id,
        query=query,
        response=response,
        model_used=model_used,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=estimated_cost,
        response_time_ms=response_time_ms
    )
    
    # 如果是第一条消息，更新对话标题
    if len(conversation.messages) == 0:
        conversation.title = query[:50]
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
