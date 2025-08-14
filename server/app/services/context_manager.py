from typing import List, Dict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain_huggingface import HuggingFaceEmbeddings

class ContextManager:
    """Manages multi-turn conversation context, intelligently filtering for relevance."""

    def __init__(self, embeddings: HuggingFaceEmbeddings, max_history: int = 5, relevance_threshold: float = 0.6):
        self.embeddings = embeddings
        self.max_history = max_history
        self.relevance_threshold = relevance_threshold

    def get_relevant_context(self, current_query: str, conversation_history: List[tuple], conversation_id: int = None, rag_service=None) -> List[tuple]:
        """
        Intelligently filters for relevant context using semantic similarity.
        Now supports conversation-level embedding caching for better performance.
        """
        if not conversation_history:
            return []

        # For short conversations, skip expensive semantic filtering
        if len(conversation_history) <= 3:
            return conversation_history

        # 1. Get the embedding for the current query using cached embedding if available
        # Format current query to match historical format for consistent semantic space
        current_query_formatted = f"Question: {current_query}"
        
        if rag_service and conversation_id is not None:
            # Use conversation-level cached embedding with formatted query
            current_embedding = rag_service.get_conversation_embedding(current_query_formatted, conversation_id)
        else:
            # Fallback to direct embedding computation
            current_embedding = self.embeddings.embed_query(current_query_formatted)

        relevant_context = []
        
        # We only consider the last N turns for efficiency.
        for query, response in conversation_history[-self.max_history:]:
            # 2. Get the embedding for the historical query+response combination using cache
            # Combine question and answer for better semantic understanding
            combined_historical_text = f"Question: {query}\nAnswer: {response}"
            
            if rag_service and conversation_id is not None:
                # Use conversation-level cached embedding for historical Q+A combinations
                hist_embedding = rag_service.get_conversation_embedding(combined_historical_text, conversation_id)
            else:
                hist_embedding = self.embeddings.embed_query(combined_historical_text)
            
            # 3. Calculate cosine similarity.
            # np.array(...).reshape(1, -1) is needed to make the vectors 2D for the function.
            similarity = cosine_similarity(
                np.array(current_embedding).reshape(1, -1),
                np.array(hist_embedding).reshape(1, -1)
            )[0][0]
            
            # 4. Only keep context that meets the relevance threshold.
            if similarity >= self.relevance_threshold:
                relevant_context.append((query, response))
        
        # The most relevant turns from the recent history are selected.
        return relevant_context