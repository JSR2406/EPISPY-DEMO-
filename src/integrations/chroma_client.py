"""ChromaDB client wrapper."""
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from ..utils.config import settings
from ..utils.logger import api_logger


class ChromaDBClient:
    """Wrapper for ChromaDB client."""
    
    def __init__(self, host: Optional[str] = None, port: int = 8000):
        self.host = host
        self.port = port
        self.client: Optional[chromadb.Client] = None
        self.collection: Optional[chromadb.Collection] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize ChromaDB client connection."""
        try:
            # Try to connect to remote ChromaDB if host is provided
            if self.host:
                chroma_url = f"http://{self.host}:{self.port}"
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                api_logger.info(f"ChromaDB client initialized: {chroma_url}")
            else:
                # Use persistent local ChromaDB
                self.client = chromadb.PersistentClient(
                    path="./data/chroma_db",
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                api_logger.info("ChromaDB client initialized (local persistent)")
            
            # Get or create collection
            try:
                self.collection = self.client.get_or_create_collection(
                    name="epidemic_data",
                    metadata={"description": "Epidemic prediction data"}
                )
            except Exception as e:
                api_logger.warning(f"Failed to get/create collection: {str(e)}")
                self.collection = None
            
            self._initialized = True
            return True
            
        except Exception as e:
            api_logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            self._initialized = False
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        if not self._initialized or not self.client:
            return []
        
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            api_logger.error(f"Failed to list collections: {str(e)}")
            return []
    
    def add_documents(
        self,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Add documents to the collection."""
        if not self._initialized or not self.collection:
            return False
        
        try:
            self.collection.add(
                documents=documents,
                ids=ids or [f"doc_{i}" for i in range(len(documents))],
                metadatas=metadatas
            )
            return True
        except Exception as e:
            api_logger.error(f"Failed to add documents: {str(e)}")
            return False
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 10
    ) -> Dict[str, Any]:
        """Query the collection."""
        if not self._initialized or not self.collection:
            return {"documents": [], "metadatas": [], "distances": []}
        
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results
            )
            return results
        except Exception as e:
            api_logger.error(f"Failed to query collection: {str(e)}")
            return {"documents": [], "metadatas": [], "distances": []}

