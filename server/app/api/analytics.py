from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any
from app.api import deps
from app.models.user import User
from app.models.conversation import Message

analytics_router = APIRouter(tags=["analytics"])

@analytics_router.get("/usage")
def get_usage_stats(
    days: int = 30,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取全局使用统计（管理员视图）
    
    返回示例：
    {
        "total_cost": "$12.3456",
        "total_queries": 234,
        "model_usage": {
            "claude-3-5-sonnet-20240620": {
                "queries": 200,
                "total_cost": "$10.00",
                "avg_cost": "$0.05"
            }
        }
    }
    """
    return get_message_usage_stats(db, user_id=None, days=days)


@analytics_router.get("/cost-summary")
def get_cost_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取全局成本摘要（管理员视图）
    """
    # 最近7天和30天的全局对比
    stats_7d = get_message_usage_stats(db, user_id=None, days=7)
    stats_30d = get_message_usage_stats(db, user_id=None, days=30)
    
    return {
        "last_7_days": {
            "total_cost": stats_7d.get("total_cost", "$0"),
            "queries": stats_7d.get("total_queries", 0)
        },
        "last_30_days": {
            "total_cost": stats_30d.get("total_cost", "$0"),
            "queries": stats_30d.get("total_queries", 0)
        }
    }


def get_message_usage_stats(
    db: Session,
    user_id: int = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    从messages表获取使用统计
    如果user_id为None，则获取所有用户的统计（管理员视图）
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 构建基础查询
    query = db.query(Message).filter(Message.created_at >= start_date)
    
    # 如果提供了user_id，需要通过conversation关联到user
    if user_id is not None:
        from app.models.conversation import Conversation
        query = query.join(Conversation).filter(Conversation.owner_id == user_id)
    
    messages = query.all()
    
    if not messages:
        return {
            "message": "No usage data available",
            "total_cost": "$0.00",
            "total_queries": 0
        }
    
    # 计算统计
    total_cost = sum(msg.estimated_cost or 0 for msg in messages)
    total_queries = len(messages)
    
    # 按模型分组统计
    model_stats = {}
    # 按用户分组统计（用于管理员视图）
    user_stats = {}
    
    for msg in messages:
        # 模型统计
        model = msg.model_used or "unknown"
        if model not in model_stats:
            model_stats[model] = {
                "count": 0,
                "cost": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
        
        model_stats[model]["count"] += 1
        model_stats[model]["cost"] += (msg.estimated_cost or 0)
        model_stats[model]["prompt_tokens"] += (msg.prompt_tokens or 0)
        model_stats[model]["completion_tokens"] += (msg.completion_tokens or 0)
        
        # 用户统计（只有在查询所有用户时才有意义）
        if user_id is None:
            from app.models.conversation import Conversation
            conversation = db.query(Conversation).filter(Conversation.id == msg.conversation_id).first()
            if conversation:
                uid = conversation.owner_id
                if uid not in user_stats:
                    user_stats[uid] = {
                        "queries": 0,
                        "cost": 0,
                        "tokens": 0
                    }
                user_stats[uid]["queries"] += 1
                user_stats[uid]["cost"] += (msg.estimated_cost or 0)
                user_stats[uid]["tokens"] += (msg.total_tokens or 0)
    
    # 每日成本趋势
    daily_costs = {}
    for msg in messages:
        date = msg.created_at.date().isoformat()
        if date not in daily_costs:
            daily_costs[date] = 0
        daily_costs[date] += (msg.estimated_cost or 0)
    
    result = {
        "period_days": days,
        "total_queries": total_queries,
        "total_cost": f"${total_cost:.4f}",
        "avg_cost_per_query": f"${(total_cost/total_queries):.4f}" if total_queries > 0 else "$0.0000",
        "model_usage": {
            model: {
                "queries": stats["count"],
                "total_cost": f"${stats['cost']:.4f}",
                "avg_cost": f"${(stats['cost']/stats['count']):.4f}" if stats['count'] > 0 else "$0.0000",
                "total_tokens": stats["prompt_tokens"] + stats["completion_tokens"]
            }
            for model, stats in model_stats.items()
        },
        "daily_cost_trend": daily_costs,
        "most_used_model": max(model_stats, key=lambda k: model_stats[k]["count"]) if model_stats else None,
        "most_expensive_day": max(daily_costs, key=daily_costs.get) if daily_costs else None
    }
    
    # 如果是全局查询（管理员视图），添加用户统计
    if user_id is None and user_stats:
        result["user_usage"] = {
            str(uid): {
                "queries": stats["queries"],
                "total_cost": f"${stats['cost']:.4f}",
                "avg_cost": f"${(stats['cost']/stats['queries']):.4f}" if stats['queries'] > 0 else "$0.0000",
                "total_tokens": stats["tokens"]
            }
            for uid, stats in user_stats.items()
        }
        result["total_users"] = len(user_stats)
    
    return result