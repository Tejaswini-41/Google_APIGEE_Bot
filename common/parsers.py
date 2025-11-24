"""
Single source of truth for parsing user requests
"""
import re
from typing import Dict, Any, List

class RequestParser:
    """Parse natural language requests into structured data"""
    
    @staticmethod
    def extract_proxy_details(message: str) -> Dict[str, Any]:
        """Extract all proxy details from user message in one go"""
        message_lower = message.lower()
        
        # Extract proxy name
        name_patterns = [
            r'named\s+([a-zA-Z0-9\-_]+)',
            r'called\s+([a-zA-Z0-9\-_]+)', 
            r'proxy\s+([a-zA-Z0-9\-_]+)',
            r'create.*?(?:proxy|api).*?named\s+([a-zA-Z0-9\-_]+)',
            r'create.*?([a-zA-Z0-9\-_]+).*?(?:proxy|api)',
            r'API proxy named\s+([a-zA-Z0-9\-_]+)',
            r'Apigee API proxy named\s+([a-zA-Z0-9\-_]+)'
        ]
        
        proxy_name = "generated-proxy"
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                proxy_name = match.group(1).replace(' ', '-')
                break
        
        # Extract target URL - FIXED TO CAPTURE FULL URL
        url_patterns = [
            r'target endpoint should be:\s*(https?://[^\s]+)',
            r'target.*?endpoint.*?(?:be|is|:)\s*(https?://[^\s]+)',
            r'pointing to\s+(https?://[^\s]+)',
            r'target.*?(https?://[^\s]+)',
            r'backend.*?(https?://[^\s]+)',
            r'endpoint.*?(https?://[^\s,;.\s]+)',
            r'(https?://[a-zA-Z0-9\-_./:]+(?:/[a-zA-Z0-9\-_./:]*)?)'
        ]
        
        target_url = "https://mocktarget.apigee.net/json"
        for pattern in url_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                url = match.group(1).rstrip('.,;')
                # Only use if it's a complete URL
                if len(url) > 10 and '.' in url:
                    target_url = url
                    break
        
        # Extract base path - IMPROVED PATTERNS
        base_path_patterns = [
            r'base path\s+([a-zA-Z0-9\-_/]+)',
            r'basepath\s+([a-zA-Z0-9\-_/]+)',
            r'path\s+([a-zA-Z0-9\-_/]+)',
            r'with base path\s+([a-zA-Z0-9\-_/]+)'
        ]
        
        base_path = f"/{proxy_name}"
        for pattern in base_path_patterns:
            match = re.search(pattern, message_lower)
            if match:
                path = match.group(1).strip('/')
                base_path = f"/{path}"
                break
        
        return {
            "name": proxy_name,
            "target_url": target_url,
            "base_path": base_path
        }
    
    @staticmethod
    def detect_policies(message: str) -> List[str]:
        """Detect required policies from message - IMPROVED DETECTION"""
        message_lower = message.lower()
        policies = []
        
        # API Key - only if explicitly mentioned
        if any(phrase in message_lower for phrase in ["api key", "apikey", "authentication", "verify api key"]):
            policies.append("VerifyAPIKey")
        
        # CORS - only if explicitly mentioned  
        if "cors" in message_lower:
            policies.append("CORS")
        
        # Quota vs Spike Arrest - be more specific
        if any(phrase in message_lower for phrase in ["quota", "rate limit", "requests per hour", "requests per day"]):
            policies.append("Quota")
            
        if any(phrase in message_lower for phrase in ["spike arrest", "spike", "burst", "requests per sec", "per second"]):
            policies.append("SpikeArrest")
            
        # JavaScript transformation
        if any(phrase in message_lower for phrase in ["javascript", "transform", "modify", "combine", "js policy"]):
            policies.append("JavaScript")
        
        # AssignMessage
        if any(phrase in message_lower for phrase in ["assign message", "set variable", "add header", "set header"]):
            policies.append("AssignMessage")
        
        return policies
    
    @staticmethod
    def extract_spike_arrest_rate(message: str) -> str:
        """Extract spike arrest rate from message"""
        message_lower = message.lower()
        
        # Look for patterns like "5 requests per sec", "10ps", "5 per second"
        rate_patterns = [
            r'(\d+)\s*requests?\s*per\s*sec',
            r'(\d+)\s*per\s*sec',
            r'(\d+)\s*per\s*second',
            r'(\d+)ps',
            r'spike arrest.*?(\d+)',
            r'(\d+)\s*req.*?sec'
        ]
        
        for pattern in rate_patterns:
            match = re.search(pattern, message_lower)
            if match:
                rate = match.group(1)
                return f"{rate}ps"
        
        return "10ps"  # default
    
    @staticmethod
    def extract_transformation_intent(message: str) -> str:
        """Extract what transformation the user wants"""
        transformation_patterns = [
            r'combine\s+([^.]+)',
            r'transform\s+([^.]+)', 
            r'modify\s+([^.]+)',
            r'add\s+([^.]+)',
            r'javascript.*?(?:to|that)\s+([^.]+)'
        ]
        
        for pattern in transformation_patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).strip()
        
        return "custom data transformation"