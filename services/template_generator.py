"""
Generate Apigee XML templates - FIXED & SIMPLIFIED VERSION
"""
from typing import Dict, Any, List
from common.parsers import RequestParser

class ApigeeTemplates:
    """Generate Apigee XML templates and JavaScript code"""
    
    @staticmethod
    def generate_proxy_xml(name: str, policies: List[str]) -> str:
        """Main proxy XML based on real Apigee structure"""
        policy_refs = "\n".join([f'  <Policy>{policy}</Policy>' for policy in policies])
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy name="{name}">
  <Description>Auto-generated proxy: {name}</Description>
  <DisplayName>{name}</DisplayName>
{policy_refs}
  <ProxyEndpoints>
    <ProxyEndpoint>default</ProxyEndpoint>
  </ProxyEndpoints>
  <Resources/>
  <TargetEndpoints>
    <TargetEndpoint>default</TargetEndpoint>
  </TargetEndpoints>
</APIProxy>'''
    
    @staticmethod
    def generate_proxy_endpoint_xml(name: str, base_path: str, policies: List[str], message: str = "") -> str:
        """Proxy endpoint XML - SIMPLIFIED, NO UNNECESSARY FAULT RULES"""
        
        # Build policy steps based on where they should execute
        preflow_request_steps = []
        preflow_response_steps = []
        postflow_response_steps = []
        
        # Map policies to execution points
        for policy in policies:
            if policy in ["VerifyAPIKey", "CORS", "AssignMessage", "SpikeArrest", "Quota"]:
                preflow_request_steps.append(f'      <Step>\n        <Name>{policy}</Name>\n      </Step>')
            elif policy in ["JavaScript"]:
                postflow_response_steps.append(f'      <Step>\n        <Name>{policy}</Name>\n      </Step>')
        
        # Format steps
        preflow_req_xml = "\n".join(preflow_request_steps) if preflow_request_steps else ""
        preflow_resp_xml = "\n".join(preflow_response_steps) if preflow_response_steps else ""
        postflow_resp_xml = "\n".join(postflow_response_steps) if postflow_response_steps else ""
        
        # Only add fault rules if VerifyAPIKey is present
        fault_rules_xml = ""
        if "VerifyAPIKey" in policies:
            fault_rules_xml = '''  <FaultRules>
    <FaultRule name="InvalidAPIKey">
      <Step>
        <Name>AM-InvalidAPIKey</Name>
      </Step>
      <Condition>(fault.name Matches "InvalidApiKeyForGivenResource") or (fault.name Matches "InvalidApiKey")</Condition>
    </FaultRule>
  </FaultRules>
  <DefaultFaultRule name="defaultRule">
    <Step>
      <Name>AM-GenericError</Name>
    </Step>
  </DefaultFaultRule>'''
        
        # Simplified flows - no CatchAll unless needed
        flows_xml = '''  <Flows>
    <Flow name="MainFlow">
      <Description>Main API flow</Description>
      <Request/>
      <Response/>
      <Condition>proxy.pathsuffix MatchesPath "/**"</Condition>
    </Flow>
  </Flows>'''
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxyEndpoint name="default">
  <Description>{name} proxy endpoint</Description>
{fault_rules_xml}
  <PreFlow name="PreFlow">
    <Request>
{preflow_req_xml}
    </Request>
    <Response>
{preflow_resp_xml}
    </Response>
  </PreFlow>
  <PostFlow name="PostFlow">
    <Request/>
    <Response>
{postflow_resp_xml}
    </Response>
  </PostFlow>
{flows_xml}
  <HTTPProxyConnection>
    <BasePath>{base_path}</BasePath>
    <Properties/>
  </HTTPProxyConnection>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>'''
    
    @staticmethod
    def generate_target_endpoint_xml(target_url: str) -> str:
        """Target endpoint XML - FIXED URL HANDLING"""
        # Clean the URL properly
        clean_url = target_url.strip().rstrip('.,; ')
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TargetEndpoint name="default">
  <Description>Default target endpoint</Description>
  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>
  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
  <Flows/>
  <HTTPTargetConnection>
    <URL>{clean_url}</URL>
    <Properties/>
  </HTTPTargetConnection>
</TargetEndpoint>'''
    
    @staticmethod
    def generate_policy_xml(policy_name: str, message: str = "") -> str:
        """Generate policy XML - DYNAMIC SPIKE ARREST RATE"""
        
        templates = {
            "VerifyAPIKey": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<VerifyAPIKey async="false" continueOnError="false" enabled="true" name="VerifyAPIKey">
  <DisplayName>Verify API Key</DisplayName>
  <APIKey ref="request.queryparam.apikey"/>
</VerifyAPIKey>''',

"JavaScript": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Javascript async="false" continueOnError="false" enabled="true" name="JavaScript">
  <DisplayName>JavaScript Transformation</DisplayName>
  <ResourceURL>jsc://transformation.js</ResourceURL>
</Javascript>''',

            
            "AssignMessage": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage continueOnError="false" enabled="true" name="AssignMessage">
  <DisplayName>Assign Message</DisplayName>
  <Properties/>
  <Set>
    <Headers>
      <Header name="X-Processed-By">Apigee</Header>
    </Headers>
  </Set>
  <AssignVariable>
    <Name>request.timestamp</Name>
    <Value>{system.timestamp}</Value>
  </AssignVariable>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <AssignTo createNew="false" transport="http" type="request"/>
</AssignMessage>''',
            
            "CORS": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<CORS async="false" continueOnError="false" enabled="true" name="CORS">
  <DisplayName>CORS Policy</DisplayName>
  <AllowOrigins>*</AllowOrigins>
  <AllowMethods>GET,POST,PUT,DELETE,OPTIONS</AllowMethods>
  <AllowHeaders>Content-Type,Authorization,X-Requested-With</AllowHeaders>
  <MaxAge>3628800</MaxAge>
  <AllowCredentials>false</AllowCredentials>
  <GeneratePreflightResponse>true</GeneratePreflightResponse>
</CORS>''',
            
            "Quota": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Quota async="false" continueOnError="false" enabled="true" name="Quota">
  <DisplayName>Quota Policy</DisplayName>
  <Allow count="1000"/>
  <Interval>1</Interval>
  <TimeUnit>hour</TimeUnit>
  <Identifier ref="client_id"/>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
</Quota>'''
        }
        
        # Handle SpikeArrest with dynamic rate
        if policy_name == "SpikeArrest":
            rate = RequestParser.extract_spike_arrest_rate(message)
            return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<SpikeArrest async="false" continueOnError="false" enabled="true" name="SpikeArrest">
  <DisplayName>Spike Arrest</DisplayName>
  <Rate>{rate}</Rate>
  <UseEffectiveCount>true</UseEffectiveCount>
</SpikeArrest>'''
        
        return templates.get(policy_name, f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<{policy_name} name="{policy_name}">
  <DisplayName>{policy_name}</DisplayName>
</{policy_name}>''')
    
    @staticmethod
    def generate_javascript_code(transformation_intent: str) -> str:
        """Generate minimal valid Apigee JavaScript (no print, no timestamps)"""

        intent_lower = transformation_intent.lower()

        if any(word in intent_lower for word in ["combine", "firstname", "lastname", "fullname"]):
            return '''// Combine firstName and lastName into fullName
    try {
        var responseContent = context.getVariable('response.content');
        if (!responseContent) return;

        var data = JSON.parse(responseContent);

        if (data.firstName && data.lastName) {
            data.fullName = data.firstName + ' ' + data.lastName;
        }

        context.setVariable('response.content', JSON.stringify(data));

    } catch (e) {
        context.setVariable('transformation.error', e.message);
    }'''
        
        else:
            return f'''// Custom transformation: {transformation_intent}
    try {{
        var responseContent = context.getVariable('response.content');
        if (!responseContent) return;

        var data = JSON.parse(responseContent);

        // Implement custom logic for: {transformation_intent}
        data.transformed = true;

        context.setVariable('response.content', JSON.stringify(data));

    }} catch (e) {{
        context.setVariable('transformation.error', e.message);
    }}'''
