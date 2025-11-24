"""
Main FastAPI application - updated for simplified structure
"""
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
import config

from models import ChatMessage, ConfirmationRequest, HealthResponse, ChatMode
from services.llm import LLMService
from services.knowledge_base import KnowledgeService  
from services.apigee_service import ApigeeService
from agents.ask_mode import AskAgent
from agents.agent_mode import AgentMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Apigee AI Assistant", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
logger.info("Initializing services...")
llm_service = LLMService()
knowledge_service = KnowledgeService(llm_service)
apigee_service = ApigeeService()

# Initialize agents
logger.info("Initializing agents...")
ask_agent = AskAgent(llm_service, knowledge_service, apigee_service)
agent_mode = AgentMode(llm_service, knowledge_service, apigee_service)

@app.post("/chat")
async def chat_with_bot(chat_message: ChatMessage):
    """Main chat endpoint"""
    
    if not config.GROQ_API_KEY:
        return {
            "response": "⚠️ Setup Required: Set GROQ_API_KEY environment variable",
            "mode": chat_message.mode,
            "success": False,
            "requires_confirmation": False
        }
    
    try:
        context = {
            "organization": chat_message.organization,
            "token": chat_message.token,
            **(chat_message.user_context or {})
        }
        
        if chat_message.mode == ChatMode.ASK:
            response = await asyncio.wait_for(
                asyncio.to_thread(ask_agent.run, chat_message.message),
                timeout=30.0
            )
            return {
                "response": response,
                "mode": chat_message.mode,
                "success": True,
                "requires_confirmation": False
            }
        else:  # AGENT mode
            response = await asyncio.wait_for(
                asyncio.to_thread(agent_mode.run, chat_message.message, context),
                timeout=45.0
            )
            return response
        
    except asyncio.TimeoutError:
        return {
            "response": "Request timeout. Please try again.",
            "mode": chat_message.mode,
            "success": False,
            "requires_confirmation": False
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "response": f"Error: {e}",
            "mode": chat_message.mode,
            "success": False,
            "requires_confirmation": False
        }

@app.post("/confirm-action")
async def confirm_action(confirmation: ConfirmationRequest):
    """Handle proxy creation confirmations"""
    if not confirmation.user_confirmation:
        return {"response": "❌ Action cancelled", "success": True}
    
    try:
        if confirmation.action == "create_proxy":
            # Use the simplified deployment method
            result = await apigee_service.deploy_to_apigee(
                confirmation.details,
                confirmation.details.get("organization"),
                confirmation.details.get("token")
            )
            return result
        else:
            return {"response": f"❌ Unknown action: {confirmation.action}", "success": False}
            
    except Exception as e:
        logger.error(f"Confirmation error: {e}")
        return {"response": f"❌ Error: {str(e)}", "success": False}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check"""
    return HealthResponse(
        status="healthy",
        llm_provider="Groq",
        api_key_configured=bool(config.GROQ_API_KEY),
        vector_store="available" if knowledge_service.is_ready() else "unavailable",
        agents="ready" if ask_agent.is_ready() and agent_mode.is_ready() else "not_ready",
        embeddings="HuggingFace"
    )

@app.get("/")
async def root():
    """API info"""
    return {
        "message": "Apigee AI Assistant - Simplified & Clean",
        "version": "2.0.0",  
        "status": "ready"
    }

if __name__ == "__main__":
    print("🚀 Starting Apigee AI Assistant (Clean & Simplified)")
    print(f"📚 Vector store: {'Ready' if knowledge_service.is_ready() else 'Not available'}")
    print(f"🤖 Agents: {'Ready' if ask_agent.is_ready() and agent_mode.is_ready() else 'Not ready'}")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)