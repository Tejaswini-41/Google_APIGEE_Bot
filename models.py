# models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class ChatMode(str, Enum):
    """Chat interaction modes"""
    ASK = "ask"
    AGENT = "agent"

class ChatMessage(BaseModel):
    """Chat message request"""
    message: str
    mode: ChatMode = ChatMode.ASK
    user_context: Optional[Dict[str, Any]] = None
    organization: Optional[str] = None
    token: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    mode: ChatMode
    success: bool
    requires_confirmation: bool = False

class ConfirmationRequest(BaseModel):
    """User confirmation request"""
    action: str
    details: Dict[str, Any]
    user_confirmation: bool

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    llm_provider: str
    api_key_configured: bool
    vector_store: str
    agents: str
    embeddings: str