import os
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from collections import OrderedDict

from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.crud import crud_job, crud_document
from app.db.session import SessionLocal
from app.services.context_manager import ContextManager

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

# QA prompt template that always includes chat history in final generation
QA_TEMPLATE = """You are a helpful AI assistant. Use the provided context and chat history to answer the question.

Context from documents:
{context}

Chat History:
{chat_history}

Question: {question}

Instructions:
1. First, check if the provided context contains information relevant to the question
2. If the context contains relevant information, use it to answer the question
3. If the context does NOT contain relevant information or is insufficient, use your general knowledge to provide a helpful answer
4. Always be clear about whether your answer comes from the provided documents or your general knowledge

Answer:"""

QA_PROMPT = PromptTemplate.from_template(QA_TEMPLATE)



class RAGService:
    # Class-level embedding model (shared across all instances)
    _embeddings = None
    _embedding_model_version = "BAAI/bge-base-en-v1.5"
    
    # Class-level conversation embedding caches (shared across all instances)
    _conversation_embedding_caches = {}
    _conversation_last_access = {}
    _cache_cleanup_counter = 0
    
    @classmethod
    def get_embeddings(cls):
        """Singleton pattern for embeddings model to avoid multiple loads."""
        if cls._embeddings is None:
            print(f"🔄 Loading embedding model: {cls._embedding_model_version}")
            
            # Create persistent cache directory for HuggingFace models
            cache_dir = "/app/model_cache"
            os.makedirs(cache_dir, exist_ok=True)
            
            model_kwargs = {"device": "cpu", "trust_remote_code": False}
            encode_kwargs = {"normalize_embeddings": True}
            cls._embeddings = HuggingFaceEmbeddings(
                model_name=cls._embedding_model_version,
                cache_folder=cache_dir,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                show_progress=False,
            )
            logger.info("Embedding model loaded successfully!")
        return cls._embeddings
    
    def __init__(self):
        # Don't initialize embeddings immediately - do it lazily when needed
        self._embeddings_initialized = False
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        
        # LRU-like cache with size limit (using OrderedDict for order tracking)
        self.vector_stores_cache: OrderedDict[int, Tuple[FAISS, datetime]] = OrderedDict()
        self.max_cache_size = 200
        self.cache_ttl = timedelta(days=30)
        
        self._context_manager = None

    @property
    def embeddings(self):
        """Lazy loading of embeddings - only initialize when actually needed"""
        if not self._embeddings_initialized:
            # Use class-level singleton to ensure consistency
            self._embeddings = self.get_embeddings()
            self._embeddings_initialized = True
            
        return self._embeddings
    
    @property
    def context_manager(self):
        """Lazy loading of ContextManager - only initialize when actually needed"""
        if self._context_manager is None:
            self._context_manager = ContextManager(
                embeddings=self.embeddings,
                max_history=5,
                relevance_threshold=0.6
            )
        return self._context_manager
    
    def get_conversation_embedding(self, query: str, conversation_id: int):
        """获取conversation级别的缓存embedding"""
        if conversation_id is None:
            # 如果没有conversation_id，直接计算不缓存
            return self.embeddings.embed_query(query)
        
        # 确保conversation缓存存在
        if conversation_id not in self._conversation_embedding_caches:
            self._conversation_embedding_caches[conversation_id] = {}
        
        conversation_cache = self._conversation_embedding_caches[conversation_id]
        
        # 检查缓存
        if query in conversation_cache:
            logger.info(f"✅ Conversation {conversation_id} 缓存命中: {query[:30]}...")
            # 更新访问时间
            self._conversation_last_access[conversation_id] = datetime.now()
            return conversation_cache[query]
        
        # 计算新embedding
        embedding = self.embeddings.embed_query(query)
        
        # 存入缓存
        conversation_cache[query] = embedding
        self._conversation_last_access[conversation_id] = datetime.now()
        
        # 定期清理（每100次调用清理一次）
        self._cache_cleanup_counter += 1
        if self._cache_cleanup_counter >= 100:
            self._cleanup_old_conversations()
            self._cache_cleanup_counter = 0
        
        return embedding
    
    @classmethod
    def _cleanup_old_conversations(cls):
        """清理长时间不活跃的conversation缓存"""
        now = datetime.now()
        max_cache_age = timedelta(hours=24)
        expired_conversations = []
        
        for conv_id, last_access in cls._conversation_last_access.items():
            if now - last_access > max_cache_age:
                expired_conversations.append(conv_id)
        
        # 删除过期的conversation缓存
        for conv_id in expired_conversations:
            if conv_id in cls._conversation_embedding_caches:
                cache_size = len(cls._conversation_embedding_caches[conv_id])
                del cls._conversation_embedding_caches[conv_id]
                del cls._conversation_last_access[conv_id]
                logger.info(f"🧹 清理过期conversation {conv_id} 缓存，包含 {cache_size} 个embedding")
    
    @classmethod 
    def get_cache_stats(cls):
        """获取全局缓存统计"""
        total_conversations = len(cls._conversation_embedding_caches)
        total_embeddings = sum(len(cache) for cache in cls._conversation_embedding_caches.values())
        
        return {
            "total_conversations": total_conversations,
            "total_cached_embeddings": total_embeddings,
            "average_embeddings_per_conversation": total_embeddings / total_conversations if total_conversations > 0 else 0
        }

    def process_document_in_background(self, file_path: str, workspace_id: int, document_id: int, job_id: str):
        """Process document and create/update vector store."""
        db = SessionLocal()
        try:
            crud_job.update_job_status(db, job_id, "processing", "Step 1/3: Loading & splitting document...")
            loader = PyPDFLoader(file_path)
            texts = self.text_splitter.split_documents(loader.load())
        
            crud_job.update_job_status(db, job_id, "processing", "Step 2/3: Generating vector embeddings...")
            
            chunk_objects_to_add = []
            for doc in texts:
                chunk_id = str(uuid.uuid4())
                
                doc.metadata.update({
                    'chunk_id': chunk_id,
                    'document_id': document_id,
                    'workspace_id': workspace_id,
                    'created_at': datetime.now().isoformat(),
                })
                chunk_objects_to_add.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "content": doc.page_content
                })
            
            crud_document.create_document_chunks(db, chunks=chunk_objects_to_add)
            vector_store_path = os.path.join(settings.VECTOR_STORE_PATH, f"workspace_{workspace_id}")
            
            if os.path.exists(vector_store_path):
                existing_store = FAISS.load_local(vector_store_path, self.embeddings, allow_dangerous_deserialization=True)
                existing_store.add_documents(texts)
                vector_store = existing_store
            else:
                vector_store = FAISS.from_documents(texts, self.embeddings)
            
            crud_job.update_job_status(db, job_id, "processing", "Step 3/3: Saving index to disk...")
            vector_store.save_local(vector_store_path)
            
            # Add to cache with automatic management
            self._add_to_cache(workspace_id, vector_store)
            crud_job.update_job_status(db, job_id, "completed", "Document processed successfully.")
        except Exception as e:
            crud_job.update_job_status(db, job_id, "failed", str(e))
        finally:
            if os.path.exists(file_path): 
                os.remove(file_path)
            db.close()

    def _load_vector_store_for_workspace(self, workspace_id: int) -> Optional[FAISS]:
        """Load vector store from cache or disk with automatic cache management."""
        
        # Check cache first
        if workspace_id in self.vector_stores_cache:
            store, timestamp = self.vector_stores_cache[workspace_id]
            
            # Check if cache entry is still valid
            if datetime.now() - timestamp < self.cache_ttl:
                # Move to end (most recently used)
                self.vector_stores_cache.move_to_end(workspace_id)
                return store
            else:
                # Expired - remove from cache
                del self.vector_stores_cache[workspace_id]
        
        # Load from disk if exists
        vector_store_path = os.path.join(settings.VECTOR_STORE_PATH, f"workspace_{workspace_id}")
        if os.path.exists(vector_store_path):
            vector_store = FAISS.load_local(vector_store_path, self.embeddings, allow_dangerous_deserialization=True)
            
            # Add to cache with eviction if needed
            self._add_to_cache(workspace_id, vector_store)
            return vector_store
        return None
    
    def _add_to_cache(self, workspace_id: int, vector_store: FAISS):
        """Add vector store to cache with LRU eviction if at capacity."""
        # Remove expired entries first
        self._clean_expired_cache()
        
        # If cache is at capacity, remove least recently used
        if len(self.vector_stores_cache) >= self.max_cache_size:
            # Remove oldest (first item in OrderedDict)
            self.vector_stores_cache.popitem(last=False)
        
        # Add new entry with timestamp
        self.vector_stores_cache[workspace_id] = (vector_store, datetime.now())
    
    def _clean_expired_cache(self):
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            k for k, (_, timestamp) in self.vector_stores_cache.items()
            if now - timestamp >= self.cache_ttl
        ]
        for k in expired_keys:
            del self.vector_stores_cache[k]
    
    def query_with_rag(
        self,
        workspace_id: int,
        query: str,
        chat_history: List[tuple] = [],
        model_name: str = "claude-3-5-sonnet-20240620",
        conversation_id: int = None
    ) -> Dict[str, Any]:
        """
        Query with RAG using recent context and question condensing.
        
        The process works as:
        1. Takes the last 5 conversation turns for context
        2. condense_question_prompt uses recent history to create standalone question
        3. Retrieves 8 most relevant document chunks
        4. LLM generates answer based on context + documents
        """
        
        vector_store = self._load_vector_store_for_workspace(workspace_id)
        
        if not vector_store:
            return {
                "answer": "You haven't uploaded any documents yet. Please upload a document to start.", 
                "sources": [], 
                "model_used": model_name
            }

        llm = ChatAnthropic(
            model=model_name,
            temperature=0.7,
            anthropic_api_key=settings.ANTHROPIC_API_KEY
        )
        
        # Step 1: Intelligent context filtering based on conversation length
        step1_start = datetime.now()
        logger.info(f"🔍 上下文分析 - conversation_id: {conversation_id}, 历史长度: {len(chat_history)}")
        
        if conversation_id and len(chat_history) > 3:
        
            logger.info(f"📊 启用语义过滤模式 (conversation_id={conversation_id}, 历史={len(chat_history)}轮)")
            # For longer conversations, use semantic similarity filtering with cached embeddings
            relevant_chat_history = self.context_manager.get_relevant_context(
                current_query=query,
                conversation_history=chat_history,
                conversation_id=conversation_id,
                rag_service=self
            )
        
            logger.info(f"🧠 语义过滤结果: {len(chat_history)} → {len(relevant_chat_history)} 轮对话")
            logger.info(f"📋 保留的对话: {[f'{q[:30]}...' for q, r in relevant_chat_history]}")
        elif chat_history:
            # For shorter conversations or without conversation_id, use simple recent context
            relevant_chat_history = chat_history[-5:]
            logger.info(f"⚡ 简单过滤模式: 取最近 {len(relevant_chat_history)} 轮对话")
            logger.info(f"📋 使用的对话: {[f'{q[:30]}...' for q, r in relevant_chat_history]}")
        else:
            relevant_chat_history = []
            logger.info("📭 无历史对话")
            
        step1_end = datetime.now()
        logger.info(f"⏱️ 上下文过滤耗时: {(step1_end - step1_start).total_seconds():.2f}s")
        
        # Step 2: Create chain with condense_question_prompt and custom QA prompt
        # This uses the recent history to create a better standalone question
        # AND includes chat history in the final answer generation
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.as_retriever(search_kwargs={"k": 8}),
            condense_question_prompt=CONDENSE_QUESTION_PROMPT,
            combine_docs_chain_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True
        )

        # Step 3: Execute with recent history
        step3_start = datetime.now()
        logger.info(f"🤖 开始LLM推理...")
        
        result = qa_chain.invoke({
            "question": query,
            "chat_history": relevant_chat_history
        })
        
        step3_end = datetime.now()
        logger.info(f"⏱️ LLM推理耗时: {(step3_end - step3_start).total_seconds():.2f}s")

        prompt_tokens = 0
        completion_tokens = 0
        if 'llm_output' in result and result['llm_output'] and 'usage' in result['llm_output']:
            usage_data = result['llm_output']['usage']
            prompt_tokens = usage_data.get('input_tokens', 0)
            completion_tokens = usage_data.get('output_tokens', 0)
        
        sources = []
        if result.get("source_documents"):
                for doc in result["source_documents"]:
                    source_info = {
                        "content": doc.page_content[:250] + "..." if len(doc.page_content) > 250 else doc.page_content,
                        "metadata": doc.metadata,
                        "chunk_id": doc.metadata.get('chunk_id'),
                        "document_id": doc.metadata.get('document_id'),
                        "workspace_id": doc.metadata.get('workspace_id'),
                    }
                    sources.append(source_info)

        return {
            "answer": result["answer"], 
            "sources": sources, 
            "model_used": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens
        }