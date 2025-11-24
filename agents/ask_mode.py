# agents/ask_mode.py
import logging
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory
from common.tools import create_common_tools
from services.llm import LLMService
from services.knowledge_base import KnowledgeService
from services.apigee_service import ApigeeService
import config

logger = logging.getLogger(__name__)

class AskAgent:
    """Ask mode agent - provides guidance and documentation"""
    
    def __init__(self, llm_service: LLMService, knowledge_service: KnowledgeService, apigee_service: ApigeeService):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
        self.apigee_service = apigee_service
        self.agent = None
        
        # Shared memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=config.MEMORY_WINDOW,
            return_messages=True
        )
        
        self._setup_agent()
    
    def _setup_agent(self):
        """Initialize the ask agent"""
        if not self.llm_service.is_ready():
            logger.warning("Cannot setup AskAgent - LLM not ready")
            return
        
        try:
            tools = create_common_tools(self.knowledge_service, self.apigee_service)
            
            system_prompt = """You are an expert Apigee API management consultant.

            CRITICAL RULES:
            1. ALWAYS use Search_Apigee_Documentation FIRST for any Apigee question
            2. Provide detailed, practical guidance with code examples
            3. Reference official documentation in responses
            4. All JavaScript code must be Apigee-compatible (Rhino ES5):
            - Use `context.getVariable('var')` to access request/response variables
            - Do NOT use browser/node functions like getRequest(), fetch(), or console.log
            - Do NOT use ES6+ syntax (let, const, arrow functions)
            5. Use other tools to provide comprehensive answers

            You help with:
            - API proxy creation and configuration
            - Security policies and other policies available
            - Rate limiting and quota management
            - JavaScript policies for transformations
            - Best practices and troubleshooting
"""
            
            self.agent = initialize_agent(
                tools,
                self.llm_service.llm_creative,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=self.memory,
                agent_kwargs={"system_message": system_prompt}
            )
            
            logger.info("AskAgent setup successfully")
            
        except Exception as e:
            logger.error(f"AskAgent setup error: {e}")
    
    def run(self, message: str) -> str:
        """Process user message"""
        if not self.agent:
            return "Ask agent not available. Please check configuration."
        
        # Enhanced prompt to force documentation search
        enhanced_message = f"""
Based on Apigee documentation and best practices, help with:

{message}

Important: Always search the knowledge base first for accurate responses.
        """
        
        try:
            return self.agent.run(
                input=enhanced_message,
                chat_history=self.memory.chat_memory.messages
            )
        except Exception as e:
            logger.error(f"AskAgent error: {e}")
            return f"Error processing request: {e}"
    
    def is_ready(self) -> bool:
        """Check if agent is ready"""
        return bool(self.agent and self.llm_service.is_ready())