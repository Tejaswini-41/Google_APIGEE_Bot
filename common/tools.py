import os
import json
import re
from typing import List, Dict, Any
from langchain.agents import Tool

class PolicyTools:
    """Policy tools using simple pattern matching"""
    
    @staticmethod
    def suggest_policies(requirements: str) -> List[str]:
        """Suggest policies based on keywords - simple and clean"""
        req = requirements.lower()
        suggested = []
        
        # Security policies
        if any(word in req for word in ["security", "api key", "apikey", "auth", "authenticate"]):
            suggested.append("VerifyAPIKey")
        
        # CORS policy
        if any(word in req for word in ["cors", "cross", "browser", "origin"]):
            suggested.append("CORS")
            
        # Rate limiting vs Spike arrest - be specific
        if any(phrase in req for phrase in ["quota", "rate limit", "limit requests"]):
            suggested.append("Quota")
            
        if any(phrase in req for phrase in ["spike arrest", "spike", "burst"]):
            suggested.append("SpikeArrest")
            
        # JavaScript transformation
        if any(word in req for word in ["javascript", "js", "script", "transform", "modify", "combine"]):
            suggested.append("JavaScript")
        
        # AssignMessage
        if any(phrase in req for phrase in ["assign message", "set variable", "add header"]):
            suggested.append("AssignMessage")
        
        return list(set(suggested))  # Remove duplicates

def create_common_tools(knowledge_service, apigee_service):
    """Create common tools for agents"""
    return [
        Tool(
            name="Search_Docs",
            func=knowledge_service.search_documentation,
            description="Search Apigee documentation"
        ),
        Tool(
            name="Suggest_Policies", 
            func=PolicyTools.suggest_policies,
            description="Suggest appropriate Apigee policies based on requirements"
        )
    ]