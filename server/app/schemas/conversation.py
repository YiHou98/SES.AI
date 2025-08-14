from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    query: str
    response: str

class MessageCreate(MessageBase):
    pass

class MessageInDB(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass
    
class ConversationInDB(ConversationBase):
    id: int
    workspace_id: int 
    created_at: datetime
    messages: list[MessageInDB] = []

    class Config:
        from_attributes = True