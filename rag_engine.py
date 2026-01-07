"""RAG Engine for orchestrating retrieval and generation."""
from typing import List, Optional, Dict
from langchain.schema import Document
from embedding_service import EmbeddingService
from vector_store import VectorStore
import config


class RAGEngine:
    """Main RAG engine that orchestrates retrieval and response generation."""
    
    def __init__(self, embedding_service: EmbeddingService, 
                 vector_store: VectorStore):
        """Initialize the RAG engine.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Store for document vectors
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    def index_documents(self, documents: List[Document]):
        """Index documents into the vector store.
        
        Args:
            documents: List of documents to index
        """
        if not documents:
            print("No documents to index")
            return
        
        print(f"Indexing {len(documents)} documents...")
        
        # Generate embeddings
        texts = [doc.page_content for doc in documents]
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Store in vector store
        self.vector_store.add_documents(documents, embeddings)
        
        print(f"Successfully indexed {len(documents)} documents")
    
    def retrieve(self, query: str, top_k: int = config.TOP_K) -> List[Document]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: Query string
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Search vector store
        results = self.vector_store.similarity_search(query_embedding, top_k)
        
        # Return documents (without scores for now)
        return [doc for doc, score in results]
    
    def generate_context(self, documents: List[Document]) -> str:
        """Generate context string from retrieved documents.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant context found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('filename', 'Unknown')
            context_parts.append(f"[Source {i}: {source}]\n{doc.page_content}")
        
        return "\n\n".join(context_parts)
    
    def query(self, question: str, top_k: int = config.TOP_K, 
              use_llm: bool = False, llm_client: Optional[any] = None) -> Dict[str, any]:
        """Query the RAG system.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            use_llm: Whether to use LLM for generation
            llm_client: Optional LLM client for generation
            
        Returns:
            Dictionary containing answer and context
        """
        # Retrieve relevant documents
        print(f"Retrieving relevant documents for: '{question}'")
        documents = self.retrieve(question, top_k)
        
        if not documents:
            return {
                'question': question,
                'answer': 'No relevant information found in the knowledge base.',
                'context': '',
                'sources': []
            }
        
        # Generate context
        context = self.generate_context(documents)
        
        # Extract sources
        sources = [doc.metadata.get('filename', 'Unknown') for doc in documents]
        
        if use_llm and llm_client:
            # Generate answer using LLM
            try:
                answer = self._generate_with_llm(question, context, llm_client)
            except Exception as e:
                print(f"Error generating with LLM: {e}")
                answer = f"Error: Could not generate answer with LLM. Retrieved context:\n\n{context}"
        else:
            # Return context without LLM generation
            answer = f"Based on the retrieved information:\n\n{context}"
        
        return {
            'question': question,
            'answer': answer,
            'context': context,
            'sources': list(set(sources))  # Unique sources
        }
    
    def _generate_with_llm(self, question: str, context: str, llm_client) -> str:
        """Generate answer using LLM (placeholder for LLM integration).
        
        Args:
            question: User's question
            context: Retrieved context
            llm_client: LLM client
            
        Returns:
            Generated answer
        """
        prompt = f"""Based on the following context, answer the question. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        # This is a placeholder - actual implementation would depend on the LLM client
        # For OpenAI:
        if hasattr(llm_client, 'chat') and hasattr(llm_client.chat, 'completions'):
            response = llm_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS
            )
            return response.choices[0].message.content
        else:
            # Fallback if LLM client doesn't match expected interface
            return f"LLM generation not configured. Context:\n\n{context}"
