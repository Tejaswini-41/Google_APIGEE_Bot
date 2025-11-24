"""
Knowledge base service - manages vector store and documentation search
"""
import os
import json
import logging
from typing import Dict, Any
from langchain_chroma import Chroma 
from langchain.chains import RetrievalQA
from langchain.schema import Document
from services.llm import LLMService
import config

logger = logging.getLogger(__name__)

class KnowledgeService:
    """Manages vector store and documentation search"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.vectorstore = None
        self.qa_chain = None
        self._setup_vectorstore()
        self._setup_qa_chain()
    
    def _setup_vectorstore(self):
        """Setup vector store from existing or create new"""
        if not self.llm_service.embeddings:
            logger.warning("No embeddings available - vector store will not be initialized")
            return
        
        try:
            if os.path.exists(config.VECTOR_DB_PATH):
                # Load existing vector store
                self.vectorstore = Chroma(
                    persist_directory=config.VECTOR_DB_PATH,
                    embedding_function=self.llm_service.embeddings
                )
                logger.info(f"Vector database loaded from {config.VECTOR_DB_PATH}")
            else:
                # Create new vector store
                self._create_vectorstore()
        except Exception as e:
            logger.error(f"Vector store setup error: {e}")
    
    def _create_vectorstore(self):
        """Create vector store from processed documentation"""
        if not os.path.exists(config.PROCESSED_DOCS_PATH):
            logger.warning(f"No processed docs found at {config.PROCESSED_DOCS_PATH}. Run data_ingestion.py first")
            return
        
        try:
            with open(config.PROCESSED_DOCS_PATH, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            if not doc_data:
                logger.warning("Processed docs file is empty")
                return
            
            # Convert to Document objects
            documents = [
                Document(page_content=item['content'], metadata=item['metadata'])
                for item in doc_data
                if item.get('content')  # Only include items with content
            ]
            
            if documents:
                self.vectorstore = Chroma.from_documents(
                    documents,
                    self.llm_service.embeddings,
                    persist_directory=config.VECTOR_DB_PATH
                )
                self.vectorstore.persist()  # Ensure persistence
                logger.info(f"Created vector store with {len(documents)} documents")
            else:
                logger.warning("No valid documents found to create vector store")
                
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
    
    def _setup_qa_chain(self):
        """Setup retrieval QA chain"""
        if not (self.vectorstore and self.llm_service.llm_precise):
            logger.warning("Cannot setup QA chain - missing vector store or LLM")
            return
            
        try:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm_service.llm_precise,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}
                ),
                return_source_documents=False
            )
            logger.info("QA chain setup successfully")
        except Exception as e:
            logger.error(f"QA chain setup error: {e}")
    
    def search_documentation(self, query: str) -> str:
        """Search documentation using RAG, fallback to LLM general knowledge"""
        if not query.strip():
            return "📚 Please provide a search query."
        
        # First try: Use knowledge base if available
        if self.qa_chain:
            try:
                result = self.qa_chain.run(query)
                
                if result and result.strip() and len(result.strip()) > 50:
                    return f"📚 **Documentation Search Result:**\n\n{result.strip()}"
                    
            except Exception as e:
                logger.error(f"Documentation search error: {e}")
        
        # Second try: Use LLM general knowledge if KB fails or no data
        return self._get_llm_response(query)
    
    def _get_llm_response(self, query: str) -> str:
        """Get response from LLM general knowledge when KB has no data"""
        if not self.llm_service.llm_precise:
            return f"""📚 **Knowledge Base Search:** {query}

❌ No data available in knowledge base and LLM service not available.

**Tip:** Make sure the knowledge base is properly initialized with documentation."""
        
        try:
            # Create a focused prompt for Apigee-related queries
            prompt = f"""You are an Apigee expert. Answer this question about Apigee API management:

Question: {query}

Please provide a helpful, accurate answer based on Apigee best practices. If you're not certain about specific details, mention that the user should verify with official Apigee documentation.

Keep the response concise but informative."""

            response = self.llm_service.llm_precise.invoke(prompt).content
            
            if response and response.strip():
                return f"""📚 **AI Knowledge Response:** *(No specific data in knowledge base)*

{response.strip()}

💡 **Note:** This response is from general AI knowledge. For the most current and specific information, please refer to the official Apigee documentation."""
            else:
                return self._get_minimal_fallback(query)
                
        except Exception as e:
            logger.error(f"LLM response error: {e}")
            return self._get_minimal_fallback(query)
    
    def _get_minimal_fallback(self, query: str) -> str:
        """Minimal fallback when everything fails"""
        return f"""📚 **Search Result:** {query}

❌ Unable to find information in knowledge base or generate AI response.

**Suggestions:**
- Check your internet connection
- Verify GROQ_API_KEY is configured correctly  
- Try rephrasing your question
- Refer to official Apigee documentation"""
    
    def search_policy_documentation(self, policy_name: str, query: str = "") -> str:
        """Search for specific policy documentation with LLM fallback"""
        if not policy_name.strip():
            return "📋 Please specify a policy name to search for."
        
        # First try: Search in vector store
        if self.vectorstore:
            try:
                search_query = f"{policy_name} policy {query}".strip()
                results = self.vectorstore.similarity_search(search_query, k=3)
                
                if results:
                    content_parts = []
                    for doc in results[:2]:
                        if doc.page_content and doc.page_content.strip():
                            content_parts.append(doc.page_content.strip())
                    
                    if content_parts:
                        content = "\n\n".join(content_parts)
                        return f"📋 **{policy_name} Policy Documentation:**\n\n{content}"
                        
            except Exception as e:
                logger.error(f"Error searching policy documentation: {e}")
        
        # Second try: Use LLM for policy information
        if self.llm_service.llm_precise:
            try:
                prompt = f"""Provide information about the Apigee {policy_name} policy.

Include:
1. What the policy does
2. Common use cases  
3. Basic configuration example (XML if applicable)
4. Key configuration parameters

Additional context: {query}

Keep the response practical and focused on real-world usage."""

                response = self.llm_service.llm_precise.invoke(prompt).content
                
                if response and response.strip():
                    return f"""📋 **{policy_name} Policy Information:** *(From AI Knowledge)*

{response.strip()}

💡 **Note:** For the most current configuration options and examples, please refer to the official Apigee policy reference documentation."""
                    
            except Exception as e:
                logger.error(f"Error getting LLM policy response: {e}")
        
        # Final fallback
        return f"""📋 **{policy_name} Policy Information**

❌ No specific information available in knowledge base or AI response.

**Suggestions:**
- Check the official Apigee policy reference documentation
- Use the agent mode to generate policy configurations
- Verify the policy name is correct"""
    
    def is_ready(self) -> bool:
        """Check if knowledge service is ready to use"""
        return bool(self.vectorstore or self.llm_service.llm_precise)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = {
            "vector_store_available": bool(self.vectorstore),
            "qa_chain_ready": bool(self.qa_chain),
            "llm_fallback_available": bool(self.llm_service.llm_precise),
            "service_ready": self.is_ready()
        }
        
        if self.vectorstore:
            try:
                collection = self.vectorstore._collection
                doc_count = collection.count() if hasattr(collection, 'count') else "unknown"
                stats["document_count"] = doc_count
                stats["vector_db_path"] = config.VECTOR_DB_PATH
            except Exception as e:
                logger.error(f"Error getting vector store stats: {e}")
                stats["document_count"] = "error"
        else:
            stats["document_count"] = 0
            
        return stats