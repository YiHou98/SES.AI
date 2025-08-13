from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.services.rag_service import RAGService

class SimilarityWeightedAttribution:
    def get_feedback_distribution(
        self,
        feedback: int, # +1 or -1
        source_chunks: List[Dict[str, Any]], # From the RAG response
        query: str,
        rag_service: RAGService # Pass in the RAG service to use its embedding model
    ) -> List[Dict[str, Any]]:
        if not source_chunks:
            return []

        query_embedding = rag_service.embeddings.embed_query(query)
        chunk_embeddings = rag_service.embeddings.embed_documents(
            [chunk['content'] for chunk in source_chunks]
        )

        # Calculate similarity scores
        similarity_scores = cosine_similarity(
            np.array(query_embedding).reshape(1, -1),
            np.array(chunk_embeddings)
        )[0]
        
        # Normalize scores to get weights
        total_similarity = np.sum(similarity_scores)
        if total_similarity == 0: # Avoid division by zero
            weights = [1 / len(source_chunks)] * len(source_chunks)
        else:
            weights = [score / total_similarity for score in similarity_scores]
        
        # Distribute feedback based on weight
        updates = []
        for chunk, weight in zip(source_chunks, weights):
            updates.append({
                "chunk_id": chunk['metadata']['chunk_id'],
                "feedback_score": feedback * weight
            })
        
        return updates

feedback_service = SimilarityWeightedAttribution()