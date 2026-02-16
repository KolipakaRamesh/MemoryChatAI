from typing import List, Dict, Any, Optional
from app.memory.base import BaseMemory
from app.config import settings as app_settings
from app.observability.logger import get_logger

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = get_logger(__name__)


class SemanticMemory(BaseMemory):
    """Semantic memory implementation using ChromaDB."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available. Semantic memory disabled.")
            return
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=app_settings.chroma_persist_dir
            ))
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection("semantic_memory_global")
                logger.info("Loaded existing semantic memory collection")
            except:
                self.collection = self.client.create_collection(
                    name="semantic_memory_global",
                    metadata={
                        "hnsw:space": "cosine",
                        "hnsw:construction_ef": 200,
                        "hnsw:search_ef": 100,
                        "hnsw:M": 16
                    }
                )
                logger.info("Created new semantic memory collection")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}. Semantic memory disabled.")
            self.client = None
            self.collection = None
    
    async def retrieve(
        self, 
        user_id: str,
        query_embedding: List[float],
        k: int = 5,
        similarity_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Retrieve semantically similar memories.
        
        Args:
            user_id: User identifier for filtering
            query_embedding: Query embedding vector
            k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            
        Returns:
            Dictionary with relevant memories and similarity scores
        """
        logger.info(f"Retrieving semantic memory for user: {user_id}")
        
        if self.collection is None:
            logger.warning("Semantic memory disabled (no ChromaDB). Returning empty.")
            return {"relevant_memories": []}
        
        try:
            # Query ChromaDB with user filter
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"user_id": user_id},
                include=["documents", "metadatas", "distances"]
            )
            
            # Filter by similarity threshold and format results
            relevant_memories = []
            
            if results['documents'] and len(results['documents'][0]) > 0:
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    if similarity_score >= similarity_threshold:
                        relevant_memories.append({
                            "content": doc,
                            "metadata": metadata,
                            "similarity_score": round(similarity_score, 3)
                        })
            
            logger.info(
                f"Retrieved {len(relevant_memories)} relevant memories "
                f"(threshold: {similarity_threshold})"
            )
            
            return {"relevant_memories": relevant_memories}
            
        except Exception as e:
            logger.error(f"Error retrieving semantic memory: {e}")
            return {"relevant_memories": []}
    
    async def store(
        self, 
        message_id: str,
        user_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Store message embedding in ChromaDB.
        
        Args:
            message_id: Unique message identifier
            user_id: User identifier
            content: Message content
            embedding: Embedding vector
            metadata: Additional metadata
        """
        try:
            if self.collection is None:
                logger.warning("Semantic memory disabled (no ChromaDB). Skipping store.")
                return
            
            # Add user_id to metadata for filtering
            metadata["user_id"] = user_id
            
            self.collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored embedding for message: {message_id}")
            
        except Exception as e:
            logger.error(f"Error storing semantic memory: {e}")
    
    async def clear(self, user_id: str) -> None:
        """
        Clear all memories for a user.
        
        Args:
            user_id: User identifier
        """
        try:
            self.collection.delete(where={"user_id": user_id})
            logger.info(f"Cleared semantic memory for user: {user_id}")
        except Exception as e:
            logger.error(f"Error clearing semantic memory: {e}")
    
    async def batch_store(
        self,
        message_ids: List[str],
        user_ids: List[str],
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        Batch store multiple embeddings for performance.
        
        Args:
            message_ids: List of message identifiers
            user_ids: List of user identifiers
            contents: List of message contents
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
        """
        try:
            # Add user_id to each metadata
            for i, user_id in enumerate(user_ids):
                metadatas[i]["user_id"] = user_id
            
            self.collection.add(
                ids=message_ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Batch stored {len(message_ids)} embeddings")
            
        except Exception as e:
            logger.error(f"Error batch storing semantic memory: {e}")
