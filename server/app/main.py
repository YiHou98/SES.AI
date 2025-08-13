from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, chat, conversations, documents, subscriptions, users, workspaces, feedback, analytics
from app.db import base_class
from app.db.session import engine
from app import models

base_class.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 预热embedding模型
@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI应用启动中...")
    print("📦 开始预热embedding模型（这可能需要10-20秒）...")
    
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def load_embedding_model():
        try:
            print("📥 正在下载/加载 BAAI/bge-base-en-v1.5 模型...")
            from app.services.rag_service import RAGService
            rag_service = RAGService()
            # 触发embedding模型加载
            _ = rag_service.embeddings
            print("✅ Embedding模型预热完成！")
            return True
        except Exception as e:
            print(f"⚠️ 模型预热失败: {e}")
            print("🔄 将在首次使用时加载模型")
            return False
    
    # 异步执行模型加载，不阻塞应用启动
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        try:
            # 设置30秒超时，避免无限等待
            await asyncio.wait_for(
                loop.run_in_executor(executor, load_embedding_model),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            print("⏰ 模型预热超时，将在首次使用时加载")
    
    print("🎉 FastAPI应用启动完成！")

# --- THIS IS THE FIX ---
# Replace the comment with the actual middleware code block.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(conversations.router, prefix=f"{settings.API_V1_STR}/conversations", tags=["Conversations"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(subscriptions.router, prefix=f"{settings.API_V1_STR}/subscriptions", tags=["Subscriptions"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(workspaces.router, prefix=f"{settings.API_V1_STR}/workspaces", tags=["Workspaces"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["Feedback"])
app.include_router(analytics.analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}