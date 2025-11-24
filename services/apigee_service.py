"""
Simplified Apigee service - FIXED VERSION
"""
import os
import json
import requests
import zipfile
import tempfile
import logging
from typing import Dict, Any, List

from common.parsers import RequestParser
from services.template_generator import ApigeeTemplates

logger = logging.getLogger(__name__)

class ApigeeService:
    """Simplified Apigee service with clear responsibilities"""
    
    def __init__(self):
        self.base_url = "https://apigee.googleapis.com/v1"
        self.org = os.getenv('APIGEE_ORG', 'apigee-non-prod-crjb')
        self.environment = os.getenv('APIGEE_ENVIRONMENT', 'apim-dev')
        self.parser = RequestParser()
        self.templates = ApigeeTemplates()
    
    def analyze_request(self, message: str) -> Dict[str, Any]:
        """Single method to analyze user request and return complete config"""
        
        # Parse basic details using parser
        proxy_details = self.parser.extract_proxy_details(message)
        
        # Detect policies using parser
        policies = self.parser.detect_policies(message)
        
        # Extract transformation intent using parser
        transformation_intent = self.parser.extract_transformation_intent(message)
        
        return {
            "proxy_details": proxy_details,
            "policies": policies,
            "transformation_intent": transformation_intent,
            "original_message": message,  # Store original message for template generation
            "custom_logic": {
                "javascript": {
                    "required": "JavaScript" in policies,
                    "description": transformation_intent,
                    "code": self.templates.generate_javascript_code(transformation_intent)
                }
            } if "JavaScript" in policies else {}
        }
    
    def generate_configuration_preview(self, message: str) -> str:
        """Generate and display complete proxy configuration"""
        
        config = self.analyze_request(message)
        proxy_details = config["proxy_details"]
        policies = config["policies"]
        original_message = config.get("original_message", message)
        
        # Generate all XMLs using templates WITH message context
        proxy_xml = self.templates.generate_proxy_xml(proxy_details["name"], policies)
        endpoint_xml = self.templates.generate_proxy_endpoint_xml(
            proxy_details["name"], 
            proxy_details["base_path"], 
            policies,
            original_message  # Pass message for context
        )
        target_xml = self.templates.generate_target_endpoint_xml(proxy_details["target_url"])
        
        # Build response
        response = f"""
🚀 **API Proxy Configuration**

**Details:**
- Name: `{proxy_details["name"]}`
- Base Path: `{proxy_details["base_path"]}` 
- Target: `{proxy_details["target_url"]}`
- Policies: `{', '.join(policies) if policies else 'None'}`

**Main Proxy XML:**
```xml
{proxy_xml}
```

**Proxy Endpoint XML:**
```xml
{endpoint_xml}
```

**Target Endpoint XML:**
```xml
{target_xml}
```
"""

        # Add policy XMLs with message context
        if policies:
            response += "\n**Policy Configurations:**\n"
            for policy in policies:
                policy_xml = self.templates.generate_policy_xml(policy, original_message)
                response += f"\n**{policy} Policy:**\n```xml\n{policy_xml}\n```\n"

        # Add JavaScript code if present
        if config.get("custom_logic", {}).get("javascript", {}).get("required"):
            js_code = config["custom_logic"]["javascript"]["code"]
            response += f"""
**JavaScript Code (transformation.js):**
```javascript
{js_code}
```
"""
        
        return response.strip()
    
    def create_proxy_bundle(self, config: Dict[str, Any]) -> bytes:
        """Create ZIP bundle from configuration"""
        
        proxy_details = config["proxy_details"]
        policies = config["policies"]
        custom_logic = config.get("custom_logic", {})
        original_message = config.get("original_message", "")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            apiproxy_dir = os.path.join(temp_dir, "apiproxy")
            for subdir in ["policies", "proxies", "targets", "resources/jsc"]:
                os.makedirs(os.path.join(apiproxy_dir, subdir), exist_ok=True)
            
            # Generate and write files
            name = proxy_details["name"]
            
            # Main proxy XML
            proxy_xml = self.templates.generate_proxy_xml(name, policies)
            with open(os.path.join(apiproxy_dir, f"{name}.xml"), 'w') as f:
                f.write(proxy_xml)
            
            # Proxy endpoint WITH message context
            endpoint_xml = self.templates.generate_proxy_endpoint_xml(
                name, proxy_details["base_path"], policies, original_message
            )
            with open(os.path.join(apiproxy_dir, "proxies", "default.xml"), 'w') as f:
                f.write(endpoint_xml)
            
            # Target endpoint
            target_xml = self.templates.generate_target_endpoint_xml(proxy_details["target_url"])
            with open(os.path.join(apiproxy_dir, "targets", "default.xml"), 'w') as f:
                f.write(target_xml)
            
            # Policy XMLs WITH message context
            for policy in policies:
                policy_xml = self.templates.generate_policy_xml(policy, original_message)
                with open(os.path.join(apiproxy_dir, "policies", f"{policy}.xml"), 'w') as f:
                    f.write(policy_xml)
            
            # JavaScript file if needed
            if custom_logic.get("javascript", {}).get("required"):
                js_code = custom_logic["javascript"]["code"]
                with open(os.path.join(apiproxy_dir, "resources/jsc", "transformation.js"), 'w') as f:
                    f.write(js_code)
            
            # Create ZIP
            bundle_path = os.path.join(temp_dir, f"{name}.zip")
            with zipfile.ZipFile(bundle_path, 'w') as zipf:
                for root, dirs, files in os.walk(apiproxy_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arc_path)
            
            # Return ZIP content
            with open(bundle_path, 'rb') as f:
                return f.read()
    
    async def deploy_to_apigee(self, config: Dict[str, Any], organization: str = None, token: str = None) -> Dict[str, Any]:
        """Deploy proxy to Apigee"""
        try:
            # Use provided credentials or defaults
            org = organization or self.org
            
            # Set token temporarily if provided
            original_token = os.getenv('APIGEE_TOKEN')
            if token:
                os.environ['APIGEE_TOKEN'] = token
            
            try:
                # Create bundle and upload
                bundle_content = self.create_proxy_bundle(config)
                name = config["proxy_details"]["name"]
                
                url = f"{self.base_url}/organizations/{org}/apis"
                files = {'file': (f'{name}.zip', bundle_content, 'application/zip')}
                
                # Make API request
                token_header = os.getenv('APIGEE_TOKEN')
                if not token_header:
                    raise Exception("No Apigee access token available")
                
                headers = {'Authorization': f'Bearer {token_header}'}
                
                response = requests.post(f"{url}?action=import&name={name}", headers=headers, files=files)
                
                if response.status_code >= 400:
                    raise Exception(f"API error {response.status_code}: {response.text}")
                
                result = response.json() if response.content else {}
                
                return {
                    "success": True,
                    "message": f"✅ Proxy '{name}' created successfully",
                    "proxy_name": name,
                    "organization": org,
                    "test_url": f"https://{org}-{self.environment}.apigee.net{config['proxy_details']['base_path']}"
                }
                
            finally:
                # Restore original token
                if token and original_token:
                    os.environ['APIGEE_TOKEN'] = original_token
                    
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return {
                "success": False,
                "message": f"❌ Failed to create proxy: {str(e)}"
            }

    # Legacy method for backward compatibility
    def generate_proxy_config(self, message: str) -> str:
        """Legacy method - use generate_configuration_preview instead"""
        return self.generate_configuration_preview(message)
