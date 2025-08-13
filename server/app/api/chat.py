from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import time

from app.api import deps
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.models.user import User
from app.core.config import settings
from app.crud import crud_conversation, crud_workspace
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

def _validate_workspace_access(user: User, workspace_id: int, db: Session):
    """验证用户对工作区的访问权限"""
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    
    workspace = crud_workspace.get_workspace(db, workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    
    return workspace

def _select_model(user: User, request: ChatRequest) -> str:
    """根据用户等级选择合适的模型"""
    if user.tier == "premium":
        return request.model or user.selected_model or settings.PREMIUM_MODEL_DEFAULT
    return settings.DEFAULT_MODEL

def _estimate_tokens(request: ChatRequest, rag_response: dict) -> tuple[int, int]:
    """估算或获取token数量"""
    prompt_tokens = rag_response.get("prompt_tokens", 0)
    completion_tokens = rag_response.get("completion_tokens", 0)
    
    # 如果没有token信息，进行粗略估算（1 token ≈ 4个字符）
    if prompt_tokens == 0:
        prompt_tokens = len(request.query) // 4
        if request.chat_history:
            for q, a in request.chat_history:
                prompt_tokens += (len(q) + len(a)) // 4
    
    if completion_tokens == 0:
        completion_tokens = len(rag_response.get("answer", "")) // 4
    
    return prompt_tokens, completion_tokens

def _calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """计算调用成本"""
    costs = settings.MODEL_COSTS.get(model, {"input": 3.00, "output": 15.00})
    input_cost = (prompt_tokens / 1_000_000) * costs["input"]
    output_cost = (completion_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 6)

def _get_or_create_conversation(request: ChatRequest, user: User, db: Session):
    """获取或创建对话"""
    if request.conversation_id:
        conversation = crud_conversation.get_conversation(db, conv_id=request.conversation_id)
        if not conversation or conversation.owner_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    else:
        return crud_conversation.create_conversation(
            db, 
            user_id=user.id,
            workspace_id=request.workspace_id
        )


@router.post("", response_model=ChatResponse)
def handle_chat(
    request: ChatRequest,
    db: Session = Depends(deps.get_db),
    rag_service: RAGService = Depends(deps.get_rag_service),
    user: User = Depends(deps.rate_limit_dependency)
):
    """
    处理聊天请求并记录成本
    """
    # 1. 验证工作区访问权限
    _validate_workspace_access(user, request.workspace_id, db)
    
    # 2. 选择模型
    model_name = _select_model(user, request)
    
    # 3. 记录开始时间并执行RAG查询
    start_time = time.time()
    rag_response = rag_service.query_with_rag(
        workspace_id=request.workspace_id,
        query=request.query,
        chat_history=request.chat_history,
        model_name=model_name,
        conversation_id=request.conversation_id
    )
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # 4. 计算token和成本
    prompt_tokens, completion_tokens = _estimate_tokens(request, rag_response)
    estimated_cost = _calculate_cost(model_name, prompt_tokens, completion_tokens)
    
    # 5. 获取或创建对话
    conversation = _get_or_create_conversation(request, user, db)
    
    # 6. 保存消息
    crud_conversation.create_message(
        db=db,
        conversation=conversation,
        query=request.query,
        response=rag_response["answer"],
        model_used=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost=estimated_cost,
        response_time_ms=response_time_ms
    )
    
    # 7. 返回响应
    rag_response['conversation_id'] = conversation.id
    return rag_response

