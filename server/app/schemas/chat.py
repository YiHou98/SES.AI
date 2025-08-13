from typing import List, Optional, Dict, Any
from pydantic import BaseModel, root_validator

class ChatRequest(BaseModel):
    query: str
    workspace_id: Optional[int] = None
    conversation_id: Optional[int] = None
    chat_history: List[tuple] = []
    model: Optional[str] = None

    @root_validator(pre=True)
    def check_ids(cls, values):
        conv_id, ws_id = values.get('conversation_id'), values.get('workspace_id')
        if conv_id is None and ws_id is None:
            raise ValueError('Either conversation_id or workspace_id must be provided')
        return values

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    model_used: str
    conversation_id: int