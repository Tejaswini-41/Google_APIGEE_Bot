# services/llm_service.py
import logging
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

logger = logging.getLogger(__name__)

class LLMService:
    """Manages LLM and embedding models"""
    
    def __init__(self):
        self.embeddings = None
        self.llm_creative = None
        self.llm_precise = None
        self._init_embeddings()
        self._init_llms()
    
    def _init_embeddings(self):
        """Initialize HuggingFace embeddings"""
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
            logger.info("HuggingFace embeddings initialized")
        except Exception as e:
            logger.error(f"Embeddings error: {e}")
    
    def _init_llms(self):
        """Initialize Groq LLMs"""
        if not config.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not found")
            return
        
        try:
            self.llm_creative = ChatGroq(
                groq_api_key=config.GROQ_API_KEY,
                model_name=config.MODEL_NAME,
                temperature=config.TEMPERATURE_CREATIVE,
                max_tokens=config.MAX_TOKENS
            )
            
            self.llm_precise = ChatGroq(
                groq_api_key=config.GROQ_API_KEY,
                model_name=config.MODEL_NAME,
                temperature=config.TEMPERATURE_PRECISE,
                max_tokens=config.MAX_TOKENS
            )
            
            logger.info(f"Groq LLMs initialized with {config.MODEL_NAME}")
        except Exception as e:
            logger.error(f"LLM error: {e}")
    
    def is_ready(self) -> bool:
        return all([self.embeddings, self.llm_creative, self.llm_precise])