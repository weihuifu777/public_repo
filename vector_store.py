"""Vector store for storing and retrieving document embeddings."""
from typing import List, Tuple, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
import config


class VectorStore:
    """Manages document storage and similarity search using ChromaDB."""
    
    def __init__(self, collection_name: str = "documents", 
                 persist_directory: Path = config.VECTOR_STORE_DIR):
        """Initialize the vector store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "RAG document collection"}
        )
        
        print(f"Vector store initialized with {self.collection.count()} documents")
    
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]):
        """Add documents with their embeddings to the store.
        
        Args:
            documents: List of Document objects
            embeddings: List of embedding vectors
        """
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        if len(documents) == 0:
            return
        
        # Prepare data for ChromaDB
        ids = [f"doc_{i}_{hash(doc.page_content)}" for i, doc in enumerate(documents)]
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"Added {len(documents)} documents to vector store")
    
    def similarity_search(self, query_embedding: List[float], 
                         top_k: int = config.TOP_K) -> List[Tuple[Document, float]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Convert results to Document objects
        documents_with_scores = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                doc = Document(
                    page_content=results['documents'][0][i],
                    metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                )
                score = results['distances'][0][i] if results['distances'] else 0.0
                documents_with_scores.append((doc, score))
        
        return documents_with_scores
    
    def clear(self):
        """Clear all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "RAG document collection"}
        )
        print("Vector store cleared")
    
    def count(self) -> int:
        """Get the number of documents in the store.
        
        Returns:
            Number of documents
        """
        return self.collection.count()
    
    def get_all_documents(self) -> List[Document]:
        """Retrieve all documents from the store.
        
        Returns:
            List of all documents
        """
        count = self.count()
        if count == 0:
            return []
        
        results = self.collection.get()
        documents = []
        for i in range(len(results['documents'])):
            doc = Document(
                page_content=results['documents'][i],
                metadata=results['metadatas'][i] if results['metadatas'] else {}
            )
            documents.append(doc)
        
        return documents
