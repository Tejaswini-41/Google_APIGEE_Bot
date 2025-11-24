"""
Few-shot prompts for AgentMode and optional XML generation.

- build_creation_prompt(user_message):
    Produces a strict JSON parsing prompt. AgentMode should call the LLM
    with this prompt and parse the returned JSON.

- build_xml_prompt(spec_or_instruction):
    Use when you want the LLM to generate full Apigee XML (APIProxy,
    ProxyEndpoint, TargetEndpoint, Policy blocks). Includes three examples:
    VerifyAPIKey, SpikeArrest multi-route, and JavaScript transformation.
"""
import json

def build_creation_prompt(user_message: str) -> str:
    schema = (
        '{"proxy_name": string, '
        '"target_url": string, '
        '"base_path": string, '
        '"policies": [string], '
        '"routes": [{"path": string, "methods": [string]}], '
        '"transformation": string}'
    )

    examples = [
        {
            "req": "Create an Apigee API proxy named booking-api with base path /booking pointing to https://backend.example.com/api. Add a VerifyAPIKey policy to all requests.",
            "json": {
                "proxy_name": "booking-api",
                "target_url": "https://backend.example.com/api",
                "base_path": "/booking",
                "policies": ["VerifyAPIKey"],
                "routes": [],
                "transformation": ""
            }
        },
        {
            "req": "Create an Apigee API proxy named googledemo with base path /google pointing to https://www.google.com. Add these routes: /getuser (GET), /adduser (POST), /updateuser (PUT), /deleteuser (DELETE). Attach SpikeArrest with 4ps.",
            "json": {
                "proxy_name": "googledemo",
                "target_url": "https://www.google.com",
                "base_path": "/google",
                "policies": ["SpikeArrest"],
                "routes": [
                    {"path": "/getuser", "methods": ["GET"]},
                    {"path": "/adduser", "methods": ["POST"]},
                    {"path": "/updateuser", "methods": ["PUT"]},
                    {"path": "/deleteuser", "methods": ["DELETE"]}
                ],
                "transformation": ""
            }
        },
        {
            "req": "Create a proxy user-transform that combines firstName and lastName into fullName in response using JavaScript. Use base path /user-transform and target https://backend.example.com/user.",
            "json": {
                "proxy_name": "user-transform",
                "target_url": "https://backend.example.com/user",
                "base_path": "/user-transform",
                "policies": ["JavaScript"],
                "routes": [],
                "transformation": "combine firstName and lastName into fullName in response"
            }
        }
    ]

    lines = [
        "You are a strict parser. Convert the user's natural language request into a single JSON object only.",
        "DO NOT output any explanation or extra text — ONLY valid JSON that matches this schema:",
        schema,
        "",
        "Examples:"
    ]
    for ex in examples:
        lines.append("Request: " + ex["req"])
        lines.append("JSON: " + json.dumps(ex["json"], ensure_ascii=False))
        lines.append("")
    lines.append("User request:")
    lines.append(user_message.strip())
    lines.append("")
    lines.append("Output only the JSON object (compact or pretty JSON is OK).")
    return "\n".join(lines)


def build_xml_prompt(spec_or_instruction: str) -> str:
    """
    Prompt the LLM to emit full Apigee XML given either:
    - a structured JSON spec (preferred), or
    - a plain instruction string.

    The LLM MUST output ONLY XML (and policy XML blocks) — no extra explanation.
    Contains 3 examples: VerifyAPIKey, SpikeArrest multi-route, JavaScript transform.
    """
    prompt = """
You are an expert Apigee API designer. Given a proxy specification or instruction, generate ONLY the XML configuration blocks below:
1) <APIProxy> main descriptor
2) <ProxyEndpoint> named "default"
3) <TargetEndpoint> named "default"
4) Individual policy XML blocks for each policy in the spec

Rules:
- Output only XML (and policy blocks). No markdown, no explanation.
- Use <RouteRule> with combined conditions only when multiple distinct routes or methods are present.
- Use deterministic policy names: VerifyAPIKey -> VerifyAPIKey, SpikeArrest -> SpikeArrest, JavaScript -> JavaScript (ResourceURL jsc://<name>.js).
- If SpikeArrest is specified with a rate, include that rate (e.g. 4ps).
- If JavaScript transformation is required, include a JavaScript policy block referencing jsc://transform.js (or jsc://<proxyname>-transform.js).

--- Example 1: VerifyAPIKey ---
Instruction:
Create an Apigee API proxy named booking-api with base path /booking pointing to https://backend.example.com/api. Add a VerifyAPIKey policy to all requests.

Expected output (XML only):
<APIProxy name="booking-api">
  <DisplayName>Booking API</DisplayName>
  <Revision>1</Revision>
  <Policies>
    <Policy>VerifyAPIKey</Policy>
  </Policies>
  <ProxyEndpoints>
    <ProxyEndpoint>default</ProxyEndpoint>
  </ProxyEndpoints>
  <TargetEndpoints>
    <TargetEndpoint>default</TargetEndpoint>
  </TargetEndpoints>
</APIProxy>

<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request>
      <Step><Name>VerifyAPIKey</Name></Step>
    </Request>
    <Response/>
  </PreFlow>
  <Flows>
    <Flow name="CatchAll">
      <Condition>proxy.pathsuffix MatchesPath "/**"</Condition>
      <Request/>
      <Response/>
    </Flow>
  </Flows>
  <HTTPProxyConnection>
    <BasePath>/booking</BasePath>
    <VirtualHost>default</VirtualHost>
  </HTTPProxyConnection>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>

<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <URL>https://backend.example.com/api</URL>
  </HTTPTargetConnection>
</TargetEndpoint>

<VerifyAPIKey name="VerifyAPIKey">
  <DisplayName>Verify API Key</DisplayName>
  <APIKey ref="request.queryparam.apikey"/>
</VerifyAPIKey>

--- Example 2: SpikeArrest with multiple routes ---
Instruction:
Create an Apigee API proxy named googledemo with base path /google pointing to https://www.google.com. Add four routes: /getuser (GET), /adduser (POST), /updateuser (PUT), /deleteuser (DELETE). Attach a SpikeArrest policy with limit 4 requests per second.

Expected output (XML only):
<APIProxy name="googledemo">
  <DisplayName>Google Demo API</DisplayName>
  <Revision>1</Revision>
  <Policies>
    <Policy>SpikeArrest</Policy>
  </Policies>
  <ProxyEndpoints><ProxyEndpoint>default</ProxyEndpoint></ProxyEndpoints>
  <TargetEndpoints><TargetEndpoint>default</TargetEndpoint></TargetEndpoints>
</APIProxy>

<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request><Step><Name>SpikeArrest</Name></Step></Request>
    <Response/>
  </PreFlow>
  <Flows>
    <Flow name="GetUser">
      <Condition>(proxy.pathsuffix MatchesPath "/getuser") and (request.verb = "GET")</Condition>
      <Request/><Response/>
    </Flow>
    <Flow name="AddUser">
      <Condition>(proxy.pathsuffix MatchesPath "/adduser") and (request.verb = "POST")</Condition>
      <Request/><Response/>
    </Flow>
    <Flow name="UpdateUser">
      <Condition>(proxy.pathsuffix MatchesPath "/updateuser") and (request.verb = "PUT")</Condition>
      <Request/><Response/>
    </Flow>
    <Flow name="DeleteUser">
      <Condition>(proxy.pathsuffix MatchesPath "/deleteuser") and (request.verb = "DELETE")</Condition>
      <Request/><Response/>
    </Flow>
    <Flow name="CatchAll">
      <Condition>proxy.pathsuffix MatchesPath "/**"</Condition>
      <Request/><Response/>
    </Flow>
  </Flows>
  <HTTPProxyConnection><BasePath>/google</BasePath><VirtualHost>default</VirtualHost></HTTPProxyConnection>
  <RouteRule name="default">
    <Condition>
      ((proxy.pathsuffix MatchesPath "/getuser") and (request.verb = "GET")) or
      ((proxy.pathsuffix MatchesPath "/adduser") and (request.verb = "POST")) or
      ((proxy.pathsuffix MatchesPath "/updateuser") and (request.verb = "PUT")) or
      ((proxy.pathsuffix MatchesPath "/deleteuser") and (request.verb = "DELETE"))
    </Condition>
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>

<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <URL>https://www.google.com</URL>
  </HTTPTargetConnection>
</TargetEndpoint>

<SpikeArrest name="SpikeArrest">
  <DisplayName>Limit 4ps</DisplayName>
  <Rate>4ps</Rate>
</SpikeArrest>

--- Example 3: JavaScript transformation ---
Instruction:
Create a proxy user-transform that combines firstName and lastName into fullName in response using JavaScript. Base path /user-transform target https://backend.example.com/user.

Expected output (XML only):
<APIProxy name="user-transform">
  <DisplayName>User Transform API</DisplayName>
  <Revision>1</Revision>
  <Policies>
    <Policy>JavaScript</Policy>
  </Policies>
  <ProxyEndpoints><ProxyEndpoint>default</ProxyEndpoint></ProxyEndpoints>
  <TargetEndpoints><TargetEndpoint>default</TargetEndpoint></TargetEndpoints>
</APIProxy>

<ProxyEndpoint name="default">
  <PreFlow name="PreFlow"><Request/><Response/></PreFlow>
  <PostFlow name="PostFlow">
    <Request/>
    <Response>
      <Step><Name>JavaScript</Name></Step>
    </Response>
  </PostFlow>
  <Flows>
    <Flow name="CatchAll">
      <Condition>proxy.pathsuffix MatchesPath "/**"</Condition>
      <Request/><Response/>
    </Flow>
  </Flows>
  <HTTPProxyConnection><BasePath>/user-transform</BasePath><VirtualHost>default</VirtualHost></HTTPProxyConnection>
  <RouteRule name="default"><TargetEndpoint>default</TargetEndpoint></RouteRule>
</ProxyEndpoint>

<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <URL>https://backend.example.com/user</URL>
  </HTTPTargetConnection>
</TargetEndpoint>

<Javascript name="JavaScript">
  <DisplayName>Transform Response</DisplayName>
  <ResourceURL>jsc://transform-fullname.js</ResourceURL>
</Javascript>

--- Now generate output for the following spec or instruction (no extra text): ---
{spec}
""".strip()
    return prompt.format(spec=spec_or_instruction)