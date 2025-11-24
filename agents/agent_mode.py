"""
Simplified agent mode - uses few‑shot LLM parsing instead of hardcoded parser
"""
import logging
import json
import re
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.memory import ConversationBufferWindowMemory
from services.llm import LLMService
from services.knowledge_base import KnowledgeService
from services.apigee_service import ApigeeService
from typing import Dict, Any
import config

from .few_shot_prompts import build_creation_prompt

logger = logging.getLogger(__name__)

class AgentMode:
    """Simplified autonomous agent for proxy creation using few-shot parsing"""
    
    def __init__(self, llm_service: LLMService, knowledge_service: KnowledgeService, apigee_service: ApigeeService):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
        self.apigee_service = apigee_service
        self.agent = None
        
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=config.MEMORY_WINDOW,
            return_messages=True
        )
        
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup agent with simple tools (keeps doc search + preview generation)"""
        if not self.llm_service.is_ready():
            logger.warning("Cannot setup AgentMode - LLM not ready")
            return
        
        try:
            tools = [
                Tool(
                    name="Search_Documentation",
                    func=self.knowledge_service.search_documentation,
                    description="Search Apigee documentation for information"
                ),
                Tool(
                    name="Generate_Proxy_Config", 
                    func=self.apigee_service.generate_configuration_preview,
                    description="Generate complete Apigee proxy configuration from user request"
                )
            ]
            
            self.agent = initialize_agent(
                tools,
                self.llm_service.llm_creative,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=3,
                early_stopping_method="generate"
            )
            
            logger.info("AgentMode setup successfully")
            
        except Exception as e:
            logger.error(f"AgentMode setup error: {e}")
    
    def run(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process user message"""
        if not self.agent:
            return {
                "response": "Agent not ready. Please check the configuration.",
                "mode": "agent",
                "success": False,
                "requires_confirmation": False
            }
        
        # Check if this is a creation request
        if self._is_creation_request(message):
            return self._handle_creation_request(message, context or {})
        
        # Regular agent interaction
        try:
            result = self.agent.run(message)
            return {
                "response": result,
                "mode": "agent", 
                "success": True,
                "requires_confirmation": False
            }
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return {
                "response": f"Error processing request: {str(e)}",
                "mode": "agent",
                "success": False,
                "requires_confirmation": False
            }
    
    def _is_creation_request(self, message: str) -> bool:
        """Simple check for creation requests (keeps previous heuristic)"""
        creation_words = ["create", "build", "generate", "make"]
        resource_words = ["proxy", "api", "endpoint"]
        
        message_lower = message.lower()
        return (any(word in message_lower for word in creation_words) and 
                any(word in message_lower for word in resource_words))
    
    def _parse_creation_request(self, message: str) -> Dict[str, Any]:
        """Use few-shot prompt + LLM to return structured config. Fallback to heuristics."""
        prompt = build_creation_prompt(message)
        llm = self.llm_service.llm_precise or self.llm_service.llm_creative

        def _call_llm(model, prompt_text):
            """Call LLM using the best available method and return raw response."""
            try:
                # Preferred new API
                if hasattr(model, "invoke"):
                    try:
                        return model.invoke({"input": prompt_text})
                    except Exception:
                        # some implementations accept a plain string
                        return model.invoke(prompt_text)
                # Common older callable wrapper
                if callable(model):
                    return model(prompt_text)
                # LangChain old API
                if hasattr(model, "generate"):
                    return model.generate([prompt_text])
            except Exception as e:
                logger.debug(f"LLM call failed: {e}")
                raise

            # Last resort
            return None

        try:
            raw = _call_llm(llm, prompt)

            # Normalize / extract text from common return shapes
            text = ""
            if raw is None:
                text = ""
            elif isinstance(raw, str):
                text = raw
            elif isinstance(raw, dict):
                # look for common keys
                for key in ("output", "text", "content", "response"):
                    if key in raw and isinstance(raw[key], str):
                        text = raw[key]
                        break
                # LangChain-style dict with generations
                if not text and "generations" in raw:
                    try:
                        gen = raw["generations"]
                        # handle nested lists
                        text = gen[0][0]["text"] if isinstance(gen, list) and isinstance(gen[0], list) else str(raw)
                    except Exception:
                        text = str(raw)
            else:
                # object-like responses (LangChain model objects)
                if hasattr(raw, "generations"):
                    try:
                        text = raw.generations[0][0].text
                    except Exception:
                        text = str(raw)
                elif hasattr(raw, "text"):
                    text = raw.text
                elif hasattr(raw, "content"):
                    text = raw.content
                else:
                    text = str(raw)

            text = (text or "").strip()

            # Extract JSON substring safely: first '{' .. last '}' if possible
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_text = text[start:end+1]
            else:
                json_text = text

            parsed = {}
            try:
                parsed = json.loads(json_text)
            except Exception as e:
                logger.debug(f"JSON parse failed from LLM output: {e}; text was: {text}")
                raise

            # Normalize keys and provide defaults
            return {
                "proxy_name": parsed.get("proxy_name") or parsed.get("name") or "generated-proxy",
                "target_url": parsed.get("target_url") or parsed.get("target") or "https://mocktarget.apigee.net/json",
                "base_path": parsed.get("base_path") or parsed.get("path") or f"/{parsed.get('proxy_name','generated-proxy')}",
                "policies": parsed.get("policies") or parsed.get("policy") or [],
                "transformation": parsed.get("transformation") or parsed.get("transform") or ""
            }

        except Exception as e:
            logger.warning(f"Few-shot parse failed ({e}), falling back to heuristics")
            # Very lightweight fallback
            fallback = {
                "proxy_name": "generated-proxy",
                "target_url": "https://mocktarget.apigee.net/json",
                "base_path": "/generated-proxy",
                "policies": [],
                "transformation": ""
            }
            # try basic url detection
            url_m = re.search(r'(https?://[^\s,;]+)', message)
            if url_m:
                fallback["target_url"] = url_m.group(1).rstrip('.,;')
            # try extract name
            name_m = re.search(r'named\s+([a-zA-Z0-9\-_]+)|called\s+([a-zA-Z0-9\-_]+)', message, re.IGNORECASE)
            if name_m:
                fallback["proxy_name"] = next(g for g in name_m.groups() if g)
                fallback["base_path"] = f"/{fallback['proxy_name']}"
            # simple policy hints
            if "cors" in message.lower():
                fallback["policies"].append("CORS")
            if "api key" in message.lower() or "apikey" in message.lower():
                fallback["policies"].append("VerifyAPIKey")
            if "spikearrest" in message.lower() or "spike arrest" in message.lower():
                fallback["policies"].append("SpikeArrest")
            return fallback
    
    def _handle_creation_request(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle proxy creation requests using ApigeeService analysis + preview.
        This ensures the confirmation payload matches what deploy_to_apigee expects.
        """
        try:
            # Use the canonical analyzer to build the config object
            config = self.apigee_service.analyze_request(message)

            # Use service preview (same format AskAgent uses)
            preview = self.apigee_service.generate_configuration_preview(message)

            # Attach UI/context details required by confirm/deploy flow
            action_details = dict(config)  # shallow copy of analyzed config
            action_details["preview"] = preview
            action_details["organization"] = context.get("organization", self.apigee_service.org)
            action_details["token"] = context.get("token")

            proxy_name = config.get("proxy_details", {}).get("name", "generated-proxy")

            return {
                "response": f"""{preview}

✅ Ready to create proxy "{proxy_name}".

To proceed with deployment to Apigee, respond with: "Yes, create this proxy"
""",
                "mode": "agent",
                "success": True,
                "requires_confirmation": True,
                "action": "create_proxy",
                "details": action_details
            }
        except Exception as e:
            logger.error(f"Creation request error: {e}")
            return {
                "response": f"Error processing creation request: {str(e)}",
                "mode": "agent",
                "success": False,
                "requires_confirmation": False
            }
    
    def is_ready(self) -> bool:
        """Check if agent is ready"""
        return bool(self.agent and self.llm_service.is_ready())