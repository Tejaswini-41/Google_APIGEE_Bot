import streamlit as st
import requests
import json
import time
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Apigee AI Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .success-box {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .code-block {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

class ApigeeAIInterface:
    def __init__(self):
        self.api_base_url = "http://localhost:8001"
        self.session_state_keys = [
            'messages', 'pending_action', 'action_details', 
            'apigee_org', 'apigee_token', 'apigee_env'
        ]
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'pending_action' not in st.session_state:
            st.session_state.pending_action = None
        if 'action_details' not in st.session_state:
            st.session_state.action_details = None
        if 'apigee_org' not in st.session_state:
            st.session_state.apigee_org = os.getenv('APIGEE_ORG', 'apigee-non-prod-crjb')
        if 'apigee_token' not in st.session_state:
            st.session_state.apigee_token = os.getenv('APIGEE_TOKEN', '')
        if 'apigee_env' not in st.session_state:
            st.session_state.apigee_env = os.getenv('APIGEE_ENVIRONMENT', 'apim-dev')
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check if the FastAPI backend is running"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "message": f"API returned {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Cannot connect to API: {str(e)}"}
    
    def send_chat_message(self, message: str, mode: str = "agent") -> Dict[str, Any]:
        """Send message to the chat API"""
        try:
            payload = {
                "message": message,
                "mode": mode,
                "user_context": {},
                "organization": st.session_state.apigee_org,
                "token": st.session_state.apigee_token
            }
            
            response = requests.post(
                f"{self.api_base_url}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "response": f"Error: API returned {response.status_code}",
                    "success": False,
                    "mode": mode
                }
        except requests.exceptions.RequestException as e:
            return {
                "response": f"Connection error: {str(e)}",
                "success": False,
                "mode": mode
            }
    
    def confirm_action(self, action: str, details: Dict[str, Any], confirmed: bool = True) -> Dict[str, Any]:
        """Confirm an action"""
        try:
            payload = {
                "action": action,
                "details": details,
                "user_confirmation": confirmed
            }
            
            response = requests.post(
                f"{self.api_base_url}/confirm-action",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "response": f"Error: API returned {response.status_code}",
                    "success": False
                }
        except requests.exceptions.RequestException as e:
            return {
                "response": f"Connection error: {str(e)}",
                "success": False
            }
    
    def render_sidebar(self):
        """Render the sidebar with configuration options"""
        st.sidebar.title("🔧 Configuration")
        
        # API Health Check
        health = self.check_api_health()
        if health.get("status") == "healthy":
            st.sidebar.success("✅ API Connected")
            st.sidebar.json(health)
        else:
            st.sidebar.error("❌ API Disconnected")
            st.sidebar.error(health.get("message", "Unknown error"))
            st.sidebar.info("Make sure FastAPI server is running on port 8001")
        
        st.sidebar.divider()
        
        # Apigee Configuration
        st.sidebar.subheader("🌐 Apigee Settings")
        
        st.session_state.apigee_org = st.sidebar.text_input(
            "Organization",
            value=st.session_state.apigee_org,
            help="Your Apigee organization name"
        )
        
        st.session_state.apigee_env = st.sidebar.text_input(
            "Environment", 
            value=st.session_state.apigee_env,
            help="Target environment (e.g., dev, test, prod)"
        )
        
        st.session_state.apigee_token = st.sidebar.text_input(
            "Access Token",
            value=st.session_state.apigee_token,
            type="password",
            help="Your Apigee access token"
        )
        
        st.sidebar.divider()
        
        # Chat Controls
        st.sidebar.subheader("💬 Chat Controls")
        
        if st.sidebar.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.pending_action = None
            st.session_state.action_details = None
            st.rerun()
        
        # Mode selection
        mode = st.sidebar.radio(
            "Assistant Mode",
            ["agent", "ask"],
            index=0,
            help="Agent mode can create proxies, Ask mode provides information only"
        )
        
        return mode
    
    def render_chat_message(self, message: Dict[str, Any]):
        """Render a chat message"""
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{content}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong><br>{content}</div>', 
                       unsafe_allow_html=True)
    
    def render_action_confirmation(self):
        """Render action confirmation UI"""
        if st.session_state.pending_action and st.session_state.action_details:
            st.markdown("### 🚨 Action Confirmation Required")
            
            action = st.session_state.pending_action
            details = st.session_state.action_details
            
            if action == "create_proxy":
                # Get proxy details safely
                proxy_details = details.get('proxy_details', {})
                proxy_name = proxy_details.get('name', 'Unknown')
                
                st.info(f"**Ready to create proxy:** {proxy_name}")
                
                # Show proxy details
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Proxy Details:**")
                    st.write(f"- Name: `{proxy_details.get('name', 'N/A')}`")
                    st.write(f"- Base Path: `{proxy_details.get('base_path', 'N/A')}`")
                    st.write(f"- Target URL: `{proxy_details.get('target_url', 'N/A')}`")
                
                with col2:
                    st.write("**Configuration:**")
                    st.write(f"- Organization: `{details.get('organization', 'N/A')}`")
                    policies = details.get('policies', [])
                    st.write(f"- Policies: `{', '.join(policies) if policies else 'None'}`")
                
                # Debug information (remove after testing)
                with st.expander("Debug Information"):
                    st.json(details)
                
                # Confirmation buttons
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("✅ Create Proxy", type="primary"):
                        with st.spinner("Creating proxy in Apigee..."):
                            result = self.confirm_action(action, details, True)
                            
                            if result.get("success"):
                                st.success(result.get("message", "Proxy created successfully!"))
                                if "test_url" in result:
                                    st.info(f"Test URL: {result['test_url']}")
                            else:
                                st.error(result.get("message", "Failed to create proxy"))
                        
                        # Clear pending action
                        st.session_state.pending_action = None
                        st.session_state.action_details = None
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.pending_action = None
                        st.session_state.action_details = None
                        st.rerun()
    
    def render_example_prompts(self):
        """Render example prompts"""
        st.markdown("### 💡 Example Prompts")
        
        examples = [
            "Create an Apigee API proxy named weather-api with base path /weather pointing to https://api.openweathermap.org/data/2.5",
            "Build a proxy that transforms firstName and lastName into fullName field using JavaScript",
            "Create a secure proxy with API key verification and CORS support",
            "Generate a proxy that adds timestamp metadata to all responses",
            "Create a proxy with rate limiting of 100 requests per minute",
            "Build a proxy that validates email format in request data"
        ]
        
        for i, example in enumerate(examples):
            if st.button(f"Example {i+1}", key=f"example_{i}"):
                return example
        
        return None
    
    def run(self):
        """Main application runner"""
        # Header
        st.markdown('<h1 class="main-header">🚀 Apigee AI Assistant</h1>', unsafe_allow_html=True)
        
        # Sidebar
        mode = self.render_sidebar()
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Chat interface
            st.markdown("### 💬 Chat with AI Assistant")
            
            # Display chat messages
            for message in st.session_state.messages:
                self.render_chat_message(message)
            
            # Action confirmation
            self.render_action_confirmation()
            
            # Chat input
            user_input = st.chat_input("Ask me to create an Apigee proxy or ask questions...")
            
            if user_input:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Send to API
                with st.spinner("Processing your request..."):
                    response = self.send_chat_message(user_input, mode)
                
                # Handle response
                assistant_message = response.get("response", "No response received")
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                
                # Check for pending actions
                if response.get("requires_confirmation") and response.get("action"):
                    st.session_state.pending_action = response.get("action")
                    st.session_state.action_details = response.get("details", {})
                
                st.rerun()
        
        with col2:
            # Example prompts
            example = self.render_example_prompts()
            if example:
                # Add example as user message and process it
                st.session_state.messages.append({"role": "user", "content": example})
                
                with st.spinner("Processing example request..."):
                    response = self.send_chat_message(example, mode)
                
                assistant_message = response.get("response", "No response received")
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                
                # Check for pending actions
                if response.get("requires_confirmation") and response.get("action"):
                    st.session_state.pending_action = response.get("action")
                    st.session_state.action_details = response.get("details", {})
                
                st.rerun()

# Run the app
if __name__ == "__main__":
    app = ApigeeAIInterface()
    app.run()