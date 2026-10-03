# ElevenLabs Agents — Server (Webhook) Tools, Client Tools, Dynamic Variables & System Variables

**Research date:** 2026-10-03
**Project:** LetterLens
**Scope:** How a backend correlates an ElevenLabs Agents tool call back to a browser session, and the exact
config shapes for webhook tools, client tools, dynamic variables and system dynamic variables.

> **Method note:** Every claim below is sourced from a doc page fetched during this research pass
> (raw `.md` via `curl -sL`, plus the live OpenAPI spec at `https://api.elevenlabs.io/openapi.json`).
> Where I could not confirm something from a primary doc, it is explicitly flagged
> **UNCONFIRMED** or **LOW CONFIDENCE**. Do not treat flagged items as verified API behaviour.

---

## 0. Naming / URL changes (important)

**"Server tools" no longer exists as a page.** The requested URL 308-redirects:

```
curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}\n" \
  "https://elevenlabs.io/docs/eleven-agents/customization/tools/server-tools.md"
# 308 -> https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md
```

Also note the whole product section moved from `/docs/conversational-ai/...` to `/docs/eleven-agents/...`
(the old `conversational-ai` path 308s to `eleven-agents`).

**Canonical pages (all verified fetched 2026-10-03):**

| Topic | URL |
| --- | --- |
| Tools overview | https://elevenlabs.io/docs/eleven-agents/customization/tools.md |
| Webhook tools (= "server tools") | https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md |
| Client tools | https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools.md |
| Dynamic variables | https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables.md |
| Overrides | https://elevenlabs.io/docs/eleven-agents/customization/personalization/overrides.md |
| Tool interruptions | https://elevenlabs.io/docs/eleven-agents/customization/tools/tool-configuration/tool-interruptions.md |
| Create tool (API reference) | https://elevenlabs.io/docs/eleven-agents/api-reference/tools/create.md |
| Agent WebSocket protocol | https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket.md |
| React SDK | https://elevenlabs.io/docs/eleven-agents/libraries/react.md |
| JavaScript SDK | https://elevenlabs.io/docs/eleven-agents/libraries/java-script.md |
| Post-call webhooks (HMAC) | https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks.md |
| Platform webhooks (HMAC) | https://elevenlabs.io/docs/eleven-api/resources/webhooks.md |
| Docs index | https://elevenlabs.io/docs/llms.txt |

`https://elevenlabs.io/docs/llms-full.txt` is **identical in size to `llms.txt` (215,130 bytes)** and is
just the index — it is *not* a full-text dump. Don't rely on it.

---

## 1. Webhook (server) tool configuration — verbatim

Source: https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md

> "**Tools** enable your assistant to connect to external data and systems. You can define a set of tools
> that the assistant has access to, and the assistant will use them where appropriate based on the
> conversation."

> "ElevenLabs agents can be equipped with tools to interact with external APIs. Unlike traditional requests,
> the assistant generates query, body, and path parameters dynamically based on the conversation and
> parameter descriptions you provide."

### 1.1 The canonical minimal tool config (verbatim from the webhook-tools page)

Saved as `tool_configs/get_weather.json`:

```json
{
  "type": "webhook",
  "name": "get_weather",
  "description": "Gets the current weather forecast for a location",
  "api_schema": {
    "url": "https://api.open-meteo.com/v1/forecast?current=temperature_2m,wind_speed_10m",
    "method": "GET",
    "path_params_schema": {
      "latitude": {
        "type": "string",
        "description": "The latitude coordinate for the requested location"
      },
      "longitude": {
        "type": "string",
        "description": "The longitude coordinate for the requested location"
      }
    }
  }
}
```

CLI add + attach:

```bash
elevenlabs tools add "get_weather" --type "webhook" --config-path ./tool_configs/get_weather.json
# then add the tool id to conversation_config.agent.prompt.tool_ids in agent_configs/<agent-name>.json
elevenlabs agents push --agent "<agent-name>"
```

### 1.2 Create via REST / SDK — verbatim

`POST https://api.elevenlabs.io/v1/convai/tools` with body `ToolRequestModel`:
- `tool_config` (required) — "Configuration for the tool"
- `response_mocks` (optional) — "Mock responses with optional parameter conditions. Evaluated top-to-bottom; first match wins."

Python (verbatim):

```python
from elevenlabs import ElevenLabs, ToolRequestModel

elevenlabs = ElevenLabs()

tool = elevenlabs.conversational_ai.tools.create(
    request=ToolRequestModel(
        tool_config={
            "type": "webhook",
            "name": "get_weather",
            "description": "Gets the current weather forecast for a location",
            "api_schema": {
                "url": "https://api.open-meteo.com/v1/forecast?current=temperature_2m,wind_speed_10m",
                "method": "GET",
                "path_params_schema": {
                    "latitude": {
                        "type": "string",
                        "description": "The latitude coordinate for the requested location",
                    },
                    "longitude": {
                        "type": "string",
                        "description": "The longitude coordinate for the requested location",
                    },
                },
            },
        }
    )
)

elevenlabs.conversational_ai.agents.update(
    agent_id="agent_7101k5zvyjhmfg983brhmhkd98n6",
    conversation_config={
        "agent": {"prompt": {"tool_ids": [tool.id]}},
    },
)
```

TypeScript (verbatim) — note it is **camelCase** in the TS SDK (`apiSchema`, `pathParamsSchema`, `toolIds`):

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

const elevenlabs = new ElevenLabsClient();

const tool = await elevenlabs.conversationalAi.tools.create({
  toolConfig: {
    type: "webhook",
    name: "get_weather",
    description: "Gets the current weather forecast for a location",
    apiSchema: {
      url: "https://api.open-meteo.com/v1/forecast?current=temperature_2m,wind_speed_10m",
      method: "GET",
      pathParamsSchema: {
        latitude: { type: "string", description: "The latitude coordinate for the requested location" },
        longitude: { type: "string", description: "The longitude coordinate for the requested location" },
      },
    },
  },
});

await elevenlabs.conversationalAi.agents.update("agent_7101k5zvyjhmfg983brhmhkd98n6", {
  conversationConfig: {
    agent: { prompt: { toolIds: [tool.id] } },
  },
});
```

Package names (verbatim from the docs): JS/TS server SDK is **`@elevenlabs/elevenlabs-js`**; Python
package is **`elevenlabs`**; browser SDKs are **`@elevenlabs/client`** and **`@elevenlabs/react`**.

### 1.3 `WebhookToolConfig` — full field list (verbatim from the Create tool API reference)

Source: https://elevenlabs.io/docs/eleven-agents/api-reference/tools/create.md — `ToolRequestModelToolConfig`, `type: webhook`

- `api_schema` (WebhookToolApiSchemaConfigInput, **required**) — "The schema for the outgoing webhoook, including parameters and URL specification" *(sic: "webhoook" typo is in the docs)*
- `description` (string, **required**) — "Description of when the tool should be used and what it does."
- `name` (string, **required**)
- `assignments` (list of DynamicVariableAssignment, optional) — "Configuration for extracting values from tool responses and assigning them to dynamic variables"
- `dynamic_variables` (DynamicVariablesConfig, optional) — "Configuration for dynamic variables"
- `execution_mode` (enum, optional, default: `immediate`) — "Determines when and how the tool executes: 'immediate' executes the tool right away when requested by the LLM, 'post_tool_speech' waits for the agent to finish speaking before executing, 'async' runs the tool in the background without blocking - best for long-running operations."
  - Allowed values: `immediate`, `post_tool_speech`, `async`
- `follow_redirects` (boolean, optional, default: `false`) — "Whether to resolve a redirect from the endpoint and return the final response. One redirect is followed, as a GET without the request body; nothing configured on this tool (headers, authentication, client certificate) is sent to the redirect target. Both the endpoint and the redirect target must use HTTPS. Not supported for API integration tools."
- `follow_redirects_allowed_domains` (list of string, optional) — "Domains a redirect may point at, e.g. 'test.example.com'. Required when following redirects, and a target outside the list is refused."
- `interruption_mode` (enum, optional, default: `allow`) — "Controls whether the user can interrupt the agent around this tool call. 'allow' (default) lets the user interrupt at any time, 'disable_during_tool' suppresses interruptions only while the tool is running, 'disable_during_tool_and_turn' suppresses interruptions while the tool runs and for the agent response that follows it."
  - Allowed values: `allow`, `disable_during_tool`, `disable_during_tool_and_turn`
- `pre_tool_speech` (enum, optional, default: `auto`) — "Controls whether the agent speaks before this tool is called. 'auto' (default) decides based on recent tool latency, 'force' always asks the agent to speak, 'off' fully opts out regardless of latency."
  - Allowed values: `auto`, `force`, `off`
- `response_timeout_secs` (integer, optional, default: **20**) — "The maximum time in seconds to wait for the tool call to complete. **Must be between 5 and 300 seconds (inclusive).**"
- `tool_call_sound` (enum, optional) — "Predefined tool call sound type to play during tool execution. If not specified, no tool call sound will be played."
  - Allowed values: `typing`, `elevator1`, `elevator2`, `elevator3`, `elevator4`
- `tool_call_sound_behavior` (enum, optional, default: `auto`) — "Determines when the tool call sound should play. 'auto' only plays when there's pre-tool speech, 'always' plays for every tool call."
  - Allowed values: `auto`, `always`
- `tool_error_handling_mode` (enum, optional, default: `auto`) — "Controls how tool errors are processed before being shared with the agent. 'auto' determines handling based on tool type (summarized for native integrations, hide for others), 'summarized' sends an LLM-generated summary, 'passthrough' sends the raw error, 'hide' does not share the error with the agent."
  - Allowed values: `auto`, `summarized`, `passthrough`, `hide`
- `disable_interruptions` (boolean, optional, default: false, **deprecated**) — "DEPRECATED: use `interruption_mode` instead."
- `force_pre_tool_speech` (boolean, optional, default: false, **deprecated**) — "DEPRECATED: use `pre_tool_speech` instead."

### 1.4 `WebhookToolApiSchemaConfigInput` — full field list (verbatim)

- `url` (string, **required**) — "The URL that the webhook will be sent to. May include path parameters, e.g. `https://example.com/agents/{agent_id}`"
- `request_headers` (map from string to WebhookToolApiSchemaConfigInputRequestHeadersValue, optional) — "Headers that should be included in the request"
- `method` (enum, optional, **default: `GET`**) — "The HTTP method to use for the webhook"
  - Allowed values: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- `path_params_schema` (map from string to LiteralJsonSchemaProperty, optional) — "Schema for path parameters, if any. The keys should match the placeholders in the URL."
- `query_params_schema` (QueryParamsJsonSchemaInput, optional) — "Schema for any query params, if any. These will be added to end of the URL as query params. Note: properties in a query param must all be literal types"
- `request_body_schema` (ObjectJsonSchemaPropertyInput, optional) — "Schema for the body parameters, if any. Used for POST/PATCH/PUT requests. The schema should be an object which will be sent as the json body"
- `response_body_schema` (ObjectJsonSchemaPropertyInput, optional) — "Schema describing the expected response body structure. **For documentation only; not surfaced to the LLM.**"
- `response_filter` (ResponseFilter, optional) — "Optional allow-list filter applied to the response before the LLM sees it, so large responses don't pollute the context. **Defaults to the full response.**"
- `content_type` (enum, optional, default: `application/json`) — "Content type for the request body. Only applies to POST/PUT/PATCH requests."
  - Allowed values: `application/json`, `application/x-www-form-urlencoded`
- `auth_resolved_params` (list of string, optional) — "URL placeholders resolved from the auth connection (e.g. secrets injected via UrlSecretAuthConnection) rather than from path_params_schema."
- `auth_connection` (WebhookToolApiSchemaConfigInputAuthConnection, optional) — "Optional auth connection to use for authentication with this webhook"

`QueryParamsJsonSchemaInput`:
- `properties` (map from string to LiteralJsonSchemaProperty, **required**)
- `required` (list of string, optional)

### 1.5 Path params vs query params vs body params

From the webhook-tools page, verbatim:

> "If the API requires path parameters, include variables in the URL path by wrapping them in curly
> braces `{}`, for example: `/api/resource/{id}` where `id` is a path parameter."

- **Path params** — single curly braces `{id}` in the `url` string; declared in `path_params_schema`, keyed
  by the placeholder name. (NB: single braces, *not* the `{{var}}` dynamic-variable syntax.)
- **Query params** — declared in `query_params_schema.properties`; "These will be added to end of the URL as
  query params. Note: properties in a query param must all be literal types". Literal query strings can also
  be written directly into `url` (the Open-Meteo example does exactly that:
  `?current=temperature_2m,wind_speed_10m`).
- **Body params** — `request_body_schema`, an `ObjectJsonSchemaPropertyInput`. "Used for POST/PATCH/PUT
  requests. The schema should be an object which will be sent as the json body."

### 1.6 How a parameter's VALUE SOURCE is declared — `LiteralJsonSchemaProperty` (verbatim)

This is the key type. **There is no field named `value_type` in the API.** Instead, the value source is
chosen by setting exactly one of five mutually-exclusive fields. The dashboard labels this choice
"value type" (e.g. `LLM Prompt`, `Dynamic variable`), but the wire format uses discrete fields.

> "Schema property for literal JSON types. **IMPORTANT: Only ONE of the following fields can be set:**
> description (LLM provides value), dynamic_variable (value from variable), is_system_provided (system
> provides value), constant_value (fixed value), or is_omitted (parameter is omitted). These are mutually
> exclusive."

- `type` (LiteralJsonSchemaPropertyType, **required**)
- `description` (string, optional, default: ``) — "The description of the property. When set, **the LLM will provide the value** based on this description. Mutually exclusive with dynamic_variable, is_system_provided, constant_value, and is_omitted."
- `enum` (list of string, optional) — "List of allowed string values for string type parameters"
- `is_system_provided` (boolean, optional, default: false) — "If true, the value will be populated by the system at runtime. Used by API Integration Webhook tools for templating. Mutually exclusive with ..."
- **`dynamic_variable` (string, optional, default: ``) — "The name of the dynamic variable to use for this property's value. Mutually exclusive with description, is_system_provided, constant_value, and is_omitted."**
- `allowed_values` (AllowedValues, optional) — "Server-side rejection guard for an LLM-provided value: the runtime rejects any value outside the permitted set this object names, and the set is not advertised to the LLM as an enum. Only supported when the value source is `description`; combining it with dynamic_variable, is_system_provided, constant_value, or is_omitted is rejected."
- `constant_value` (LiteralJsonSchemaPropertyConstantValue, optional) — "A constant value to use for this property. Mutually exclusive with description, dynamic_variable, is_system_provided, and is_omitted."
- `is_omitted` (boolean, optional, default: false) — "If true, this parameter will be completely omitted from the request. Only valid for optional parameters. Mutually exclusive with ..."
- `allowed_values_dynamic_variable` (string, optional, **deprecated**) — "DEPRECATED: use `allowed_values` instead. When set, the LLM provides the value but the runtime rejects any value not present in the list held by this dynamic variable (must be a JSON array such as [\"ws_alpha\", \"ws_beta\"]) ..."

`AllowedValues`:
- `dynamic_variable` (string, **required**) — "Name of a dynamic variable that must resolve to a JSON array of permitted values, e.g. [\"ws_alpha\", \"ws_beta\"]. System variables work only if they resolve to a list."

`ObjectJsonSchemaPropertyInput` (the body schema) has the same value-source mechanism at object level:
- `property_kind` (enum, optional, default: `object`) — allowed: `array`, `object`
- `description` (string, optional, default: ``)
- `dynamic_variable` (string, optional, default: ``) — "When set, **the entire parameter is populated from this dynamic variable at runtime**. Mutually exclusive with description (LLM-provided value), constant_value, and is_omitted."
- `constant_value` (map from string to any, optional) — "When set, the entire object uses this constant JSON value at runtime."
- `is_omitted` (boolean, optional, default: false)
- `type` (`"object"`, optional)
- `required` (list of string, optional)
- `properties` (map from string to ObjectJsonSchemaPropertyInputPropertiesValue, optional)
- `required_constraints` (RequiredConstraints, optional) — "Wrapper for anyOf/allOf composition constraints scoped to required fields." → `any_of` / `all_of` lists of `RequiredConstraint`.

`ArrayJsonSchemaPropertyOutput` similarly supports `dynamic_variable`, `constant_value`, `is_omitted`,
`items`.

### 1.7 Headers — exact type (from the live OpenAPI spec)

`https://api.elevenlabs.io/openapi.json` → `components.schemas["WebhookToolApiSchemaConfig-Input"].properties.request_headers`, **verbatim**:

```json
{
  "additionalProperties": {
    "anyOf": [
      { "type": "string" },
      { "$ref": "#/components/schemas/ConvAISecretLocator" },
      { "$ref": "#/components/schemas/ConvAIDynamicVariable" },
      { "$ref": "#/components/schemas/ConvAIEnvVarLocator" }
    ]
  },
  "type": "object",
  "title": "Request Headers",
  "description": "Headers that should be included in the request"
}
```

So a header value is **either** a plain string **or** one of three locator objects:

```json
{ "secret_id": "<id>" }                 // ConvAISecretLocator  — "Used to reference a secret from the agent's secret store."
{ "variable_name": "<name>" }           // ConvAIDynamicVariable — "Used to reference a dynamic variable."
{ "env_var_label": "<label>" }          // ConvAIEnvVarLocator  — "Used to reference an environment variable by label."
```

(Note the OpenAPI spelling is `ConvAISecretLocator` / `ConvAIDynamicVariable`; the docs-site API reference
page renders them as `ConvAiSecretLocator` / `ConvAiDynamicVariable`. Same thing.)

### 1.8 Content type

> "Configure the format for request body encoding:
> * **JSON** (default): Sends body parameters as `application/json`
> * **URL-encoded**: Sends body parameters as `application/x-www-form-urlencoded`"
>
> "The content type setting only applies to POST, PUT, and PATCH requests with body parameters."

### 1.9 Response handling — does the agent get the raw JSON body back?

**Yes, by default the agent sees the full response body.** Evidence (verbatim, Create tool API reference):

> `response_filter` (ResponseFilter, optional) — "Optional allow-list filter applied to the response before
> the LLM sees it, so large responses don't pollute the context. **Defaults to the full response.**"

`ResponseFilter`:
- `mode` (enum, optional, default: `all`) — "Controls how tool responses are filtered. **'all' returns entire response**, 'allow' returns only specified paths, 'hide_all' hides the entire response."
  - Allowed values: `all`, `allow`, `hide_all`
- `filters` (list of string, optional) — "Dot notation paths to include when mode is 'allow' (e.g., ['ticket.id', 'ticket.status'])."
- `content_type` (`"application/json"`, optional) — "Content type for response filtering. Only 'application/json' responses are filtered."

And `response_body_schema` is documentation-only: "**For documentation only; not surfaced to the LLM.**"

**Practical implication for LetterLens:** whatever JSON your endpoint returns lands in the LLM context
verbatim unless you set `response_filter`. Keep responses small and LLM-friendly, or set
`mode: "allow"` with explicit `filters`.

---

## 2. Dynamic variables

Source: https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables.md

> "**Dynamic variables** allow you to inject runtime values into your agent's messages, system prompts, and
> tools. This enables you to personalize each conversation with user-specific data without creating multiple
> agents."

> "Dynamic variables can be integrated into multiple aspects of your agent:
> * **System prompts** to customize behavior and context
> * **First messages** to personalize greetings
> * **Tool parameters and headers** to pass user-specific data"

### 2.1 Reference syntax in prompts — `{{variable_name}}`

> "Add variables using double curly braces `{{variable_name}}` in your:
> * System prompts
> * First messages
> * Tool parameters"

Troubleshooting section, verbatim:

> "Verify that:
> * Variable names match exactly (case-sensitive)
> * Variables use double curly braces: `{{ variable_name }}`
> * Variables are included in your dynamic_variables object"

### 2.2 Declaring placeholders / defaults in the agent config

> "Set `conversation_config.agent.dynamic_variables.dynamic_variable_placeholders`. Each key is the variable
> name; the value is the placeholder used during testing:"

```json
{
  "conversation_config": {
    "agent": {
      "dynamic_variables": {
        "dynamic_variable_placeholders": {
          "user_name": "Angelo",
          "account_type": "premium"
        }
      }
    }
  }
}
```

`DynamicVariablesConfig` (API reference): `dynamic_variable_placeholders` (map from string to any, optional)
— "A dictionary of dynamic variable placeholders and their values".

> "Configure default values for testing without passing variables at runtime."

**Note:** there is no separate "declare the variable" step beyond placeholders — you just reference
`{{name}}` and pass the value at session start. Placeholders exist for testing/defaults.

Python / TS agent update (verbatim):

```python
elevenlabs.conversational_ai.agents.update(
    agent_id="agent_7101k5zvyjhmfg983brhmhkd98n6",
    conversation_config={
        "agent": {
            "dynamic_variables": {
                "dynamic_variable_placeholders": {
                    "user_name": "Angelo",
                    "account_type": "premium",
                }
            }
        },
    },
)
```

```typescript
await elevenlabs.conversationalAi.agents.update("agent_7101k5zvyjhmfg983brhmhkd98n6", {
  conversationConfig: {
    agent: {
      dynamicVariables: {
        dynamicVariablePlaceholders: { user_name: "Angelo", account_type: "premium" },
      },
    },
  },
});
```

### 2.3 Setting dynamic variables AT SESSION START from the client

Browser JS (**verbatim** from the dynamic-variables page — this is the one LetterLens needs):

```javascript
import { Conversation } from '@elevenlabs/client';

class VoiceAgent {
  ...

  async startConversation() {
    try {
        // Request microphone access
        await navigator.mediaDevices.getUserMedia({ audio: true });

        this.conversation = await Conversation.startSession({
            agentId: 'agent_id_goes_here', // Replace with your actual agent ID

            dynamicVariables: {
                user_name: 'Angelo'
            },

            ... add some callbacks here
        });
    } catch (error) {
        console.error('Failed to start conversation:', error);
        alert('Failed to start conversation. Please ensure microphone access is granted.');
    }
  }
}
```

Python (verbatim):

```python
dynamic_vars = {
    "user_name": "Angelo",
}

config = ConversationInitiationData(
    dynamic_variables=dynamic_vars
)

conversation = Conversation(
    elevenlabs,
    agent_id,
    config=config,
    requires_auth=bool(api_key),
    audio_interface=DefaultAudioInterface(),
    ...
)
conversation.start_session()
```

Swift (verbatim):

```swift
let dynamicVars: [String: DynamicVariableValue] = [
  "customer_name": .string("John Doe"),
  "account_balance": .number(5000.50),
  "user_id": .int(12345),
  "is_premium": .boolean(true)
]

let config = SessionConfig(
    agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6",
    dynamicVariables: dynamicVars
)
let conversation = try await Conversation.startSession(config: config)
```

Embedded widget (verbatim):

```html
<elevenlabs-convai
  agent-id="agent_7101k5zvyjhmfg983brhmhkd98n6"
  dynamic-variables='{"user_name": "John", "account_type": "premium"}'
></elevenlabs-convai>
```

**Wire format (authoritative).** From the Agent WebSocket API reference
(https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket.md), the
`ConversationInitiationClientData` client→server message schema includes, verbatim:

```yaml
        dynamic_variables:
          type: object
          additionalProperties:
            description: Any type
        type:
          type: string
          enum:
            - conversation_initiation_client_data
      title: ConversationInitiationClientData
```

Other fields on the same message: `conversation_config_override` (via overrides), `custom_llm_extra_body`
(**UNCONFIRMED — not seen in the fetched excerpt**), `environment` ("Environment to use for resolving
environment variables"), `starting_workflow_node_id`, `procedure_ids`.

So at the protocol level, the first message after socket open is:

```json
{
  "type": "conversation_initiation_client_data",
  "dynamic_variables": { "letterlens_session_id": "abc123" }
}
```

**React SDK (`@elevenlabs/react`)** — the React SDK page lists `useConversation` options as
`clientTools`, `overrides`, `textOnly`, `serverLocation`, and documents `startSession({ agentId, userId,
signedUrl, conversationToken, connectionType })`. It does **not** mention `dynamicVariables` anywhere.
The page does state: "`@elevenlabs/react` re-exports everything from `@elevenlabs/client`, so you don't
need to install [it separately]". **CONFIDENCE: MEDIUM** that `startSession({ dynamicVariables })` works
identically in `@elevenlabs/react` — strongly implied by the re-export and by the shared wire protocol, but
**not documented on the React page**. If LetterLens uses `@elevenlabs/react`, verify empirically on first run.

### 2.4 Supported value types

> "Dynamic variables support these value types:
> #### String — Text values
> #### Number — Numeric values
> #### Boolean — True/false values"

And: "Ensure that: Variable values match the expected type; **Values are strings, numbers, or booleans only**."

(Caveat: `preserve_native_type` on `DynamicVariableAssignment` and `AllowedValues` both refer to list-valued
dynamic variables, so lists exist internally — but the documented client-settable types are string/number/boolean.)

### 2.5 Secret dynamic variables — `secret__` prefix

> "Secret dynamic variables are populated in the same way as normal dynamic variables but indicate to our
> ElevenAgents that these should only be used in dynamic variable headers and never sent to an LLM provider
> as part of an agent's system prompt or first message.
>
> We recommend using these for auth tokens or private IDs that should not be sent to an LLM. To create a
> secret dynamic variable, simply prefix the dynamic variable with `secret__`."

> **Warning:** "Secret values are returned redacted as `<REDACTED>`, including in post-call webhooks and the
> conversations API. Don't use the `secret__` prefix for values you need to read back after the
> conversation. Pass those as regular dynamic variables, or pass a non-sensitive identifier and look up the
> sensitive value on your own system."

**LetterLens implication:** if you pass a browser-session token as `secret__letterlens_token`, it can only
be used in headers and you will **not** be able to read it back from the conversations API or post-call
webhook. For correlation keys you want to see later, use a plain dynamic variable.

### 2.6 Updating dynamic variables from tool responses — `assignments`

> "[Tool calls] can create or update dynamic variables if they return a valid JSON object. To specify what
> should be extracted, set the object path(s) using dot notation. If the field or path doesn't exist, nothing
> is updated.
>
> Example of a response object and dot notation:
> * Status corresponds to the path: `response.status`
> * The first user's email in the users array corresponds to the path: `response.users.0.email`"

The doc's own example JSON (reproduced verbatim — **note it is syntactically invalid JSON as published**,
an object key inside an array; treat the path semantics, not the literal, as the source of truth):

```json
{
  "response": {
    "status": 200,
    "message": "Successfully found 5 users",
    "users": [
      "user_1": {
        "user_name": "test_user_1",
        "email": "test_user_1@email.com"
      }
    ]
  }
}
```

> "Assignments are a field of each webhook tool, documented [here](/docs/eleven-agents/api-reference/tools/create#response.body.tool_config.SystemToolConfig.assignments)."

`DynamicVariableAssignment` (verbatim, API reference):
- `dynamic_variable` (string, **required**) — "The name of the dynamic variable to assign the extracted value to"
- `value_path` (string, **required**) — "Dot notation path to extract the value from the source (e.g., 'user.name' or 'data.0.id')"
- `source` (`"response"`, optional) — "The source to extract the value from. Currently only 'response' is supported."
- `sanitize` (boolean, optional, default: false) — "If true, this assignment's value will be removed from the tool response before sending to the LLM and transcript, but still processed for variable assignment."
- `preserve_native_type` (boolean, optional, default: false) — "If true, non-scalar values (lists, objects) extracted from the tool response are stored as their native type instead of being stringified to JSON. Enable this to use extracted arrays directly as list dynamic variables."

> "Note system tools cannot update dynamic variables." (client-tools page)

### 2.7 Public talk-to page URL parameters (bonus)

Two methods, both verbatim from the dynamic-variables page:

1. Base64-encoded JSON in `vars`:
   `https://elevenlabs.io/app/talk-to?agent_id=agent_...&vars=eyJ1c2VyX25hbWUiOiJKb2huIiwiYWNjb3VudF90eXBlIjoicHJlbWl1bSJ9`
2. Individual `var_`-prefixed query params:
   `https://elevenlabs.io/app/talk-to?agent_id=agent_...&var_user_name=John&var_account_type=premium`

> "When both methods are used simultaneously, individual `var_` parameters take precedence over the
> base64-encoded variables to prevent conflicts."

---

## 3. SYSTEM DYNAMIC VARIABLES — complete verbatim list

Source: https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables.md
Section: "## System dynamic variables"

> "Your agent has access to these automatically available system variables:"

| Variable | Doc description (verbatim) |
| --- | --- |
| `system__agent_id` | "Unique identifier of the agent that initiated the conversation (stays stable throughout the conversation)" |
| `system__current_agent_id` | "Unique identifier of the currently active agent (changes after agent transfers)" |
| `system__caller_id` | "Caller's phone number (voice calls only)" |
| `system__called_number` | "Destination phone number (voice calls only)" |
| `system__call_duration_secs` | "Call duration in seconds" |
| `system__time_utc` | "Current UTC time (ISO format)" |
| `system__time` | "Current time in the specified timezone (human-readable format, e.g., \"Friday, 12:33 12 December 2025\")" |
| `system__timezone` | "User-provided timezone (must be valid for tzinfo)" |
| **`system__conversation_id`** | **"ElevenLabs' unique conversation identifier"** |
| `system__call_sid` | "Call SID (twilio calls only)" |
| `system__call_id` | "Unique identifier for the SIP trunk call (SIP trunk calls only)" |
| `system__agent_turns` | "The total number of conversation turns the agent has taken during this conversation." |
| `system__current_agent_turns` | "The number of conversation turns the current agent has taken. Resets whenever the conversation transfers to a different agent." |
| `system__current_subagent_turns` | "The number of conversation turns the current subagent has taken. Resets whenever the workflow transitions to a different node." |
| `system__is_text_only` | "True if the conversation operates in text-only mode, false otherwise." |
| `system__conversation_history` | "JSON-serialized representation of the current conversation history. Lazily evaluated at the moment it is referenced." |

That is the **complete** documented list (16 variables) as of 2026-10-03.

Properties, verbatim:

> "System variables:
> * Are available without runtime configuration
> * Are prefixed with `system__` (reserved prefix)
> * Are updated automatically throughout the conversation"
>
> **Warning:** "Custom dynamic variables cannot use the reserved `system__` prefix."

### 3.1 `system__conversation_history` format (verbatim)

```json
{
  "x-elevenlabs-history": true,
  "entries": [
    { "role": "user", "message": "Hello" },
    { "role": "agent", "message": "Hi, how can I help?" },
    {
      "role": "agent",
      "tool_requests": [{ "tool_name": "lookup_order", "params_as_json": { "order_id": "123" } }]
    },
    {
      "role": "tool",
      "tool_results": [{ "tool_name": "lookup_order", "result_value": "{\"status\": \"shipped\"}" }]
    }
  ]
}
```

> "Each entry includes a `role` (`\"user\"`, `\"agent\"`, or `\"tool\"`) and one of:
> * `message` — the text content of the turn
> * `tool_requests` — an array of tool calls made by the agent, with resolved parameter values
> * `tool_results` — an array of tool responses
>
> If a tool result or parameter contains a nested conversation history, it is redacted to a placeholder
> (e.g. `[conversation_history (5 turns)]`) to avoid unbounded recursive expansion."
>
> "This variable is useful for passing conversation context to tools (e.g. webhooks, custom LLMs) or for
> including conversation history in sub-agent prompts during handoffs."

### 3.2 Matching the conversation ID on the browser side

The same ID is available to the browser, so correlation is two-sided:

- React SDK, `getId` (verbatim):
  ```js
  const { getId } = useConversation();
  const conversationId = getId();
  console.log(conversationId); // e.g., "conv_9001k1zph3fkeh5s8xg9z90swaqa"
  ```
  → source: https://elevenlabs.io/docs/eleven-agents/libraries/react.md
- `startSession` return value (verbatim): "`startSession` returns a promise resolving a `conversationId`.
  The value is a globally unique conversation ID you can use to identify separate conversations."
- JS SDK: `const id = conversation.getId();`
- WebSocket: server sends `conversation_initiation_metadata` whose
  `conversation_initiation_metadata_event.conversation_id` (string, required) carries the ID.

**ID format observed in docs:** `conv_9001k1zph3fkeh5s8xg9z90swaqa` (prefix `conv_`).

---

## 4. Can a server tool's request BODY include a dynamic variable (e.g. the conversation ID)?

**Yes — but NOT by writing `{{system__conversation_id}}` as a literal string in a JSON body template.**
You declare the body property with `dynamic_variable: "system__conversation_id"` and ElevenLabs substitutes
the runtime value. The resulting HTTP body your backend receives is
`{"session_id": "conv_9001k1zph3..."}`.

### 4.1 Doc evidence (quoted)

1. Dynamic-variables page, "Overview": *"Dynamic variables can be integrated into multiple aspects of your
   agent: ... **Tool parameters and headers** to pass user-specific data"* and *"**Passing data** to tool
   calls"*.
2. Dynamic-variables page, "Define dynamic variables in tools": *"You can also define dynamic variables in
   the tool configuration. To create a new dynamic variable, **set the value type to Dynamic variable** and
   click the `+` button."*
3. Create tool API reference, `LiteralJsonSchemaProperty`: *"`dynamic_variable` (string, optional) — **The
   name of the dynamic variable to use for this property's value.** Mutually exclusive with description,
   is_system_provided, constant_value, and is_omitted."*
4. Create tool API reference, `ObjectJsonSchemaPropertyInput` (= `request_body_schema`):
   *"`dynamic_variable` (string, optional) — **When set, the entire parameter is populated from this dynamic
   variable at runtime.**"*
5. System variables are *"available without runtime configuration"* and *"updated automatically throughout
   the conversation"*, with `system__conversation_id` = *"ElevenLabs' unique conversation identifier"*.
6. Corroborating use of a system variable where a value is substituted into config:
   `voicemail_detection.voicemail_message` — *"Supports dynamic variables (e.g., `{{system__time}}`,
   `{{system__call_duration_secs}}`, `{{custom_variable}}`)."*

### 4.2 The config LetterLens should use (constructed from the verified schema)

```json
{
  "type": "webhook",
  "name": "save_letter_insight",
  "description": "Stores an insight extracted from the user's letter. Call this whenever the user confirms a fact about their letter.",
  "response_timeout_secs": 20,
  "api_schema": {
    "url": "https://api.letterlens.app/agent/insight",
    "method": "POST",
    "content_type": "application/json",
    "request_headers": {
      "X-LetterLens-Token": { "secret_id": "<workspace_secret_id>" }
    },
    "request_body_schema": {
      "type": "object",
      "properties": {
        "session_id": {
          "type": "string",
          "dynamic_variable": "system__conversation_id"
        },
        "letterlens_session_id": {
          "type": "string",
          "dynamic_variable": "letterlens_session_id"
        },
        "insight": {
          "type": "string",
          "description": "The insight to store, phrased as a short complete sentence."
        }
      },
      "required": ["session_id", "insight"]
    }
  }
}
```

Your backend then receives, verbatim on the wire:

```json
{
  "session_id": "conv_9001k1zph3fkeh5s8xg9z90swaqa",
  "letterlens_session_id": "ll_7f2a...",
  "insight": "The letter is a council tax arrears notice dated 12 September."
}
```

**CONFIDENCE:**
- `request_body_schema` + per-property `dynamic_variable` → **HIGH** (explicit API schema field with
  explicit semantics; corroborated by the dashboard "value type = Dynamic variable" instruction).
- `system__conversation_id` being a valid name for that `dynamic_variable` field → **MEDIUM-HIGH**. System
  variables are documented as ordinary dynamic variables with a reserved prefix, and the `AllowedValues`
  type explicitly says "System variables work only if they resolve to a list", which confirms system
  variables are accepted in `dynamic_variable`-style fields. **I did not find a doc page that shows
  `"dynamic_variable": "system__conversation_id"` literally inside a `request_body_schema`.** Smoke-test on
  first integration.
- Writing a literal `"{{system__conversation_id}}"` string into a body template → **LOW CONFIDENCE / likely
  wrong.** The body is a JSON *schema*, not a template, and the docs show `{{...}}` only for prompts, first
  messages and free-text config strings. Do not build on it.

### 4.3 Belt-and-braces recommendation for LetterLens

Pass your **own** session id from the browser as a dynamic variable at `startSession`, *and* send
`system__conversation_id`:

```javascript
const sessionId = crypto.randomUUID();           // your own key, generated in the browser
const conversation = await Conversation.startSession({
  agentId: "agent_...",
  dynamicVariables: { letterlens_session_id: sessionId },
  clientTools: { /* ... */ },
});
const conversationId = conversation.getId();      // "conv_..." — post to your backend to join the two
```

That gives the backend two independent correlation keys and removes the single point of failure.

---

## 5. Client tools

Source: https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools.md

> "**Client tools** enable your assistant to execute client-side functions. Unlike [webhook tools], client
> tools allow the assistant to perform actions such as triggering browser events, running client-side
> functions, or sending notifications to a UI."

### 5.1 Config file (verbatim)

```json
{
  "type": "client",
  "name": "logMessage",
  "description": "Use this client-side tool to log a message to the user's client.",
  "expects_response": false,
  "parameters": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "The message to log in the console."
      }
    },
    "required": ["message"]
  }
}
```

```bash
elevenlabs tools add "logMessage" --type "client" --config-path ./tool_configs/log_message.json
```

Note the field is `parameters` (an `ObjectJsonSchemaProperty`), **not** `api_schema`:
> `parameters` (ObjectJsonSchemaPropertyInput, optional) — "Schema for any parameters to pass to the client"

### 5.2 `expects_response` / "Wait for response" — exact semantics

API reference, verbatim:

> `expects_response` (boolean, optional, **default: `false`**) — "If true, calling this tool should **block
> the conversation until the client responds** with some response which is passed to the llm. If false then
> we will continue the conversation without waiting for the client to respond, this is useful to show
> content to a user but not block the conversation"

Client-tools page, verbatim:

> "### Passing client tool results to the conversation context
>
> When you want your agent to receive data back from a client tool, ensure that you tick the **Wait for
> response** option in the tool configuration."
>
> "Once the client tool is added, when the function is called the agent will wait for its response and append
> the response to the conversation context."

React SDK page, verbatim:

> "If the function returns a value, it is passed back to the agent as a response."
>
> "The tool **must be explicitly set to block the conversation** in the ElevenLabs UI for the agent to await
> and react to the response. **Otherwise, the agent assumes success and continues the conversation.**"

So: **the handler's return value is only consumed if `expects_response: true` / "Wait for response" is on.**

Timeout for client tools differs from webhook tools:
> `response_timeout_secs` (integer, optional, default: **20**) — "The maximum time in seconds to wait for the
> tool call to complete. **Must be between 1 and 120 seconds (inclusive).**"

### 5.3 Registering handlers in the browser (verbatim)

`@elevenlabs/client`:

```javascript
// ...
const conversation = await Conversation.startSession({
  // ...
  clientTools: {
    logMessage: async ({message}) => {
      console.log(message);
    }
  },
  // ...
});
```

Returning data to the agent (verbatim):

```javascript
const clientTools = {
  getCustomerDetails: async () => {
    // Fetch customer details (e.g., from an API)
    const customerData = {
      id: 123,
      name: "Alice",
      subscription: "Pro"
    };
    // Return data directly to the agent.
    return customerData;
  }
};

// Start the conversation with client tools configured.
const conversation = await Conversation.startSession({ clientTools });
```

`@elevenlabs/react` — `useConversation` option (verbatim):

```ts
const conversation = useConversation({
  clientTools: {
    displayMessage: (parameters: { text: string }) => {
      alert(parameters.text);

      return "Message displayed";
    },
  },
});
```

`@elevenlabs/react` — `<ConversationProvider clientTools={{...}}>` is also supported (shown on the React
page), and there is a per-component hook (verbatim):

```tsx
import { useConversationClientTool } from "@elevenlabs/react";
import { useState } from "react";

function MapComponent() {
  const [location, setLocation] = useState({ lat: 0, lng: 0 });

  useConversationClientTool("getLocation", () => {
    return `${location.lat},${location.lng}`;
  });

  useConversationClientTool("setLocation", (params: { lat: number; lng: number }) => {
    setLocation(params);
    return "Location updated";
  });

  return <Map center={location} />;
}
```

> "A hook for dynamically registering client tools from React components. **Tools are automatically
> unregistered when the component unmounts.** ... The hook always uses the latest closure value of the
> handler, so you don't need to worry about stale state."

Install (verbatim): `npm install @elevenlabs/react` — "`@elevenlabs/react` re-exports everything from
`@elevenlabs/client`, so you don't need to install [it]". Plain JS: `npm install @elevenlabs/client`.

### 5.4 Async support

Three independent mechanisms:

1. **Handlers may be `async`** — the documented JS examples use `async ({message}) => {...}` and
   `async () => {...}`, and the Swift signature is `{ parameters async throws -> String? }`.
2. **`execution_mode`** (on client, webhook and other tool types) — verbatim: "'immediate' executes the tool
   right away when requested by the LLM, '`post_tool_speech`' waits for the agent to finish speaking before
   executing, '`async`' runs the tool in the background without blocking - best for long-running operations."
3. **`expects_response: false`** — fire-and-forget; the agent does not wait.

### 5.5 Client-tool protocol on the wire (from the WebSocket API reference)

Server → client, `ClientToolCall`:

```yaml
    ClientToolCallClientToolCall:
      type: object
      properties:
        tool_name:
          type: string
        tool_call_id:
          type: string
        parameters:
          type: object
          additionalProperties:
            description: Any type
        event_id:
          type: integer
        expects_response:
          type: boolean
          description: Whether the server expects a ClientToolResult response.
      required:
        - tool_name
        - tool_call_id
        - parameters
        - event_id
        - expects_response
```

Client → server, `ClientToolResult`:

```yaml
    ClientToolResult:
      type: object
      properties:
        type:
          type: string
          enum:
            - client_tool_result
        tool_call_id:
          type: string
          description: ID of the tool call this result corresponds to.
        result:
          type: string
        is_error:
          type: boolean
        error_type:
          $ref: '#/components/schemas/ClientToolResultErrorType'
          description: >-
            Optional category for the failure reason. When set, `is_error` is
            treated as true. `user_rejected` is special-cased to mark the tool
            as not having been called.
      required:
        - tool_call_id
        - result
        - is_error
```

`ClientToolResultErrorType` allowed values (verbatim, partial list captured):
`... external_server, external_client, customer_auth, client_timeout, unknown` (plus `user_rejected`,
referenced in the description above). **The leading values of this enum were truncated in my capture —
treat the list as incomplete (LOW CONFIDENCE on completeness).**

Case-sensitivity warning (verbatim, client-tools page):
> "The tool and parameter names in the agent configuration are case-sensitive and **must** match those
> registered in your code."

Relevant SDK callback: `onUnhandledClientToolCall` — "handler called when an unhandled client tool call is
encountered."

---

## 6. Webhook (server) tool security & auth

Source: https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md, "## Supported Authentication Methods"

> "ElevenLabs Agents supports multiple authentication methods to securely connect your tools with external
> APIs. Authentication methods are configured in your agent settings and then connected to individual tools
> as needed."

| Method | Doc text (verbatim, condensed) |
| --- | --- |
| **OAuth2 Client Credentials** | "Automatically handles the OAuth2 client credentials flow. Configure with your client ID, client secret, and token URL (e.g., `https://api.example.com/oauth/token`). Optionally specify scopes as comma-separated values and additional JSON parameters. Set up by clicking **Add Auth** on **Workspace Auth Connections** on the **Agent** section of your agent settings page." |
| **OAuth2 JWT** | "Uses JSON Web Token authentication for OAuth 2.0 JWT Bearer flow. Requires your JWT signing secret, token URL, and algorithm (default: HS256). Configure JWT claims including issuer, audience, and subject. Optionally set key ID, expiration (default: 3600 seconds), scopes, and extra parameters." |
| **Basic Authentication** | "Simple username and password authentication for APIs that support HTTP Basic Auth." |
| **Bearer Tokens** | "Token-based authentication that adds your bearer token value to the request header. Configure by adding a header to the tool configuration, **selecting *Secret* as the header type, and clicking *Create New Secret***." |
| **Custom Headers** | "Add custom authentication headers with any name and value for proprietary authentication methods. Configure by adding a header to the tool configuration and specifying its **name** and **value**." |

Plus, from the API reference:
- `auth_connection` on `api_schema` — "Optional auth connection to use for authentication with this webhook".
  Referenced by `AuthConnectionLocator` → `{ "auth_connection_id": "<id>" }` ("Used to reference an auth
  connection from the workspace's auth connection store"), or `EnvironmentAuthConnectionLocator` →
  `{ "env_var_label": "<label>" }` ("References an environment variable of type 'auth_connection' by label.
  At runtime, resolves to the auth connection for the current environment, falling back to the default
  environment.").
- `auth_resolved_params` — "URL placeholders resolved from the auth connection (e.g. secrets injected via
  UrlSecretAuthConnection) rather than from path_params_schema."

> **Warning (verbatim, webhook-tools page):** "An API key is not required for this tool. If one is required,
> this should be passed in the headers and stored as a secret."

### 6.1 Is there an HMAC signature on server-tool requests? — **NO documented evidence**

**This is the most important correction to the brief.** HMAC signing with the `ElevenLabs-Signature` header
is documented for **post-call webhooks and platform webhooks** — i.e. events ElevenLabs sends you when a
call *ends* — **not** for webhook/server **tool** calls made mid-conversation.

Post-call webhooks page (verbatim):

> "It is important for the listener to validate all incoming webhooks. Webhooks currently support
> authentication via HMAC signatures. Set up HMAC authentication by:
> * Securely storing the shared secret generated upon creation of the webhook
> * **Verifying the ElevenLabs-Signature header** in your endpoint using the SDK"
>
> "The JavaScript SDK exposes `constructEvent`; the Python SDK exposes `construct_event` with **`rawBody`**,
> **`sig_header`**, and **`secret`** (these are not named `payload` / `signature` in Python). Both verify the
> signature, validate the timestamp, and parse the JSON payload."

Header name as read in code (lowercased, per HTTP convention):

```python
signature = request.headers.get("elevenlabs-signature")
event = elevenlabs.webhooks.construct_event(
    rawBody=...,            # raw request body
    sig_header=signature,
    secret=WEBHOOK_SECRET,
)
```

```javascript
const signature = req.headers['elevenlabs-signature'];
event = await elevenlabs.webhooks.constructEvent(payload, signature, WEBHOOK_SECRET);
// Express: use express.text() to preserve raw body for signature verification
// Next.js:  const signature = req.headers.get('elevenlabs-signature');
```

Also: "Using IP allowlisting in combination with HMAC signature validation provides multiple layers of
[security]."

**Exact canonical header casing:** the prose says **`ElevenLabs-Signature`**; the code reads
`elevenlabs-signature`. HTTP headers are case-insensitive, so match case-insensitively.

**`t=`/`v0=` signature payload format: UNCONFIRMED.** I did not find the signed-string construction
documented on the fetched pages — the docs steer you to the SDK's `constructEvent` /
`construct_event` rather than hand-rolling. Use the SDK.

**For LetterLens server tools, authenticate with a shared-secret header** (Custom Header / Secret header
type, or `{"secret_id": "..."}` in `request_headers`). Do not expect a signature to verify.

---

## 7. Timeouts, slow tools, and errors

### 7.1 Timeout

| Tool type | `response_timeout_secs` default | Range (verbatim) |
| --- | --- | --- |
| **webhook** | 20 | "Must be between **5 and 300** seconds (inclusive)." |
| **client** | 20 | "Must be between **1 and 120** seconds (inclusive)." |
| **system** | 20 | (no range stated in docs) |

### 7.2 What the agent says/does while a tool is slow

- `pre_tool_speech` (default `auto`): "Controls whether the agent speaks before this tool is called. 'auto'
  (default) **decides based on recent tool latency**, 'force' always asks the agent to speak, 'off' fully
  opts out regardless of latency." → set `force` if you want a guaranteed "let me check that for you".
- `tool_call_sound` + `tool_call_sound_behavior`: ambient audio (`typing`, `elevator1`–`elevator4`) during
  execution; `auto` "only plays when there's pre-tool speech", `always` "plays for every tool call".
  > "You can configure ambient audio to play during tool execution to enhance the user experience."
- `execution_mode: "async"`: "runs the tool in the background without blocking - best for long-running
  operations."
- `interruption_mode`: see §7.4.

### 7.3 What the agent does when a tool errors

`tool_error_handling_mode` (default `auto`), verbatim:

> "Controls how tool errors are processed before being shared with the agent. 'auto' determines handling
> based on tool type (**summarized for native integrations, hide for others**), 'summarized' sends an
> LLM-generated summary, 'passthrough' sends the raw error, 'hide' does not share the error with the agent."

**So with the default `auto`, a custom webhook tool's error is HIDDEN from the agent.** If LetterLens wants
the agent to be able to say "I couldn't save that, let me try again", set
`tool_error_handling_mode: "summarized"` (or `"passthrough"` for debugging). This is a real footgun: with
`hide`, the agent gets nothing and will likely hallucinate success.

The transcript/observability side exposes a status enum, `AgentToolResponseAgentToolResponseStatus`
(verbatim): `success`, `error`, `blocked`, `skipped` — "Tool call status derived from execution flags."
`AgentToolResponse` carries `tool_name`, `tool_call_id`, `tool_type`, `is_error`, `is_blocked` (default
false), `event_id`, `is_called`, `status`.

**What the agent literally *says* on timeout/failure: UNCONFIRMED.** No doc page states a canned phrase.
Behaviour is governed by `tool_error_handling_mode` plus the system prompt. Write explicit failure
instructions into the system prompt.

### 7.4 Interruption modes during tool execution

Source: https://elevenlabs.io/docs/eleven-agents/customization/tools/tool-configuration/tool-interruptions.md

> "By default a user can interrupt the agent at any point, including while a tool is executing."
>
> "The `interruption_mode` field controls this per tool. It is available on **webhook tools, client tools,
> system tools, and MCP servers**."

| Value | Dashboard label | Behavior (verbatim) |
| --- | --- | --- |
| `allow` | Allow | "The user can interrupt the agent at any time. This is the default." |
| `disable_during_tool` | Disable during execution | "Interruptions are suppressed only while the tool runs. The agent response that follows can be interrupted." |
| `disable_during_tool_and_turn` | Disable during whole turn | "Interruptions are suppressed while the tool runs and for the agent response that follows it." |

> "When several tools run in parallel, **the strictest mode among them applies** for that turn."
>
> "The boolean `disable_interruptions` field is deprecated. ... `disable_interruptions: true` is equivalent
> to `interruption_mode: \"disable_during_tool_and_turn\"`"

CLI example (verbatim):

```json
{
  "type": "webhook",
  "name": "confirm_payment",
  "description": "Confirms a pending payment",
  "interruption_mode": "disable_during_tool_and_turn"
}
```

---

## 8. Response mocking (useful for LetterLens dev/testing)

From the Create tool API reference, `response_mocks` on `ToolRequestModel`:
> "Mock responses with optional parameter conditions. Evaluated top-to-bottom; first match wins."

`ToolResponseMockConfigInput`:
- `mock_result` (string, **required**) — "The return value the LLM sees when this mock is active."
- `parameter_conditions` (list of UnitTestToolCallParameter, optional) — "If the list is empty, the mock will always activate."
- `is_error` (boolean, optional, default: false) — "If true, the mock result is surfaced to the LLM as a tool error rather than a successful result."

`UnitTestToolCallParameter`: `eval` (required), `path` (required). `eval` variants: `type: anything`;
`type: exact` + `expected_value` ("The exact string value that the parameter must match."); `type: llm` +
`description`; `type: regex`.

---

## 9. LLM choice (affects tool-call reliability)

Warning repeated verbatim on both the webhook-tools and client-tools pages:

> "When using tools, we recommend picking high intelligence models like **GPT 5.2, Gemini-2.5-Flash, or
> Claude Sonnet 4.5** and avoiding **Gemini-2.0-Flash**."

> "It's important to note that the choice of LLM matters to the success of function calls. Some LLMs can
> struggle with extracting the relevant parameters from the conversation."

---

## 10. Other API endpoints / regions noted in passing

Create tool: `POST https://api.elevenlabs.io/v1/convai/tools`

Servers (verbatim):
- `https://api.elevenlabs.io` (Production, default)
- `https://api.us.elevenlabs.io` (Production US)
- `https://api.eu.residency.elevenlabs.io` (Production EU)
- `https://api.in.residency.elevenlabs.io` (Production India)
- `https://api.sg.residency.elevenlabs.io` (Production Singapore)

Session auth endpoints (verbatim from React SDK page):
- WebSocket signed URL: `GET https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=...`
  with header `xi-api-key` → response field `signed_url`
- WebRTC token: `GET https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=...`
  with header `xi-api-key` → response field `token`
- Raw WebSocket URL: `wss://api.elevenlabs.io/v1/convai/conversation`

> "The connection type is automatically inferred based on the conversation mode. Voice conversations use
> WebRTC and text-only conversations use WebSocket by default."

`serverLocation` option: `"us"` (default), `"eu-residency"`, `"in-residency"`, `"global"`.

---

## 11. Blockers / gotchas for the LetterLens build

1. **`tool_error_handling_mode` defaults to `auto`, which HIDES errors from a custom webhook tool.** Set it
   to `"summarized"` explicitly or the agent will narrate success after a failed save.
2. **No HMAC signature on server-tool requests.** Only post-call/platform webhooks are signed
   (`ElevenLabs-Signature`). Use a shared-secret header for tool-call auth and treat that secret as the
   whole of the trust boundary.
3. **The request body is a JSON *schema*, not a string template.** `{"session_id": "{{system__conversation_id}}"}`
   as a literal body template is **not** the documented mechanism; use
   `{"type": "string", "dynamic_variable": "system__conversation_id"}` on the property.
4. **`@elevenlabs/react` does not document `dynamicVariables`.** The option is documented only for
   `@elevenlabs/client`'s `Conversation.startSession`. Verify on first run; fall back to `@elevenlabs/client`
   directly if needed.
5. **`secret__`-prefixed dynamic variables are unreadable afterwards** (`<REDACTED>` in post-call webhooks
   and the conversations API) and are usable only in headers. Don't use the prefix for a correlation key.
6. **Default webhook timeout is 20s, floor is 5s.** A cold-start serverless backend plus an LLM call can blow
   past that. Raise `response_timeout_secs` and/or use `execution_mode: "async"` for non-blocking writes.
7. **Full tool responses go into LLM context by default.** Return terse JSON or configure `response_filter`
   with `mode: "allow"`.
8. **`method` defaults to `GET`** — easy to forget on a POST tool.
9. **Path placeholders use single braces `{id}`; prompt variables use double braces `{{var}}`.** Different
   mechanisms, easy to conflate.
10. **Tool and parameter names are case-sensitive** and must match the client registration exactly.
11. **`llms-full.txt` is not a full dump** — it's the same index as `llms.txt`. Fetch individual `.md` pages.
12. **Old URLs 308-redirect**: `/docs/conversational-ai/...` → `/docs/eleven-agents/...`, and
    `.../tools/server-tools.md` → `.../tools/webhook-tools.md`. `curl -sL` (follow redirects) is required.

---

## 12. Source URLs used (all fetched 2026-10-03)

- https://elevenlabs.io/docs/llms.txt
- https://elevenlabs.io/docs/eleven-agents/customization/tools.md
- https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md
- https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools.md
- https://elevenlabs.io/docs/eleven-agents/customization/tools/tool-configuration/tool-interruptions.md
- https://elevenlabs.io/docs/eleven-agents/customization/tools/tool-configuration/tool-call-sounds.md
- https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables.md
- https://elevenlabs.io/docs/eleven-agents/customization/personalization/overrides.md
- https://elevenlabs.io/docs/eleven-agents/api-reference/tools/create.md
- https://elevenlabs.io/docs/eleven-agents/api-reference/eleven-agents/websocket.md
- https://elevenlabs.io/docs/eleven-agents/libraries/react.md
- https://elevenlabs.io/docs/eleven-agents/libraries/java-script.md
- https://elevenlabs.io/docs/eleven-agents/libraries/web-sockets.md
- https://elevenlabs.io/docs/eleven-agents/workflows/post-call-webhooks.md
- https://elevenlabs.io/docs/eleven-api/resources/webhooks.md
- https://api.elevenlabs.io/openapi.json (live OpenAPI spec, 2,252,803 bytes)

### Pages identified but NOT fetched (open leads)

- https://elevenlabs.io/docs/eleven-agents/customization/tools/code-tools.md — "Run custom JavaScript logic directly on ElevenLabs' infrastructure." Possible alternative to a webhook round-trip.
- https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/update-state.md — "Let your agent update dynamic variables mid-conversation using expressions."
- https://elevenlabs.io/docs/eleven-agents/integrate/environment-variables.md — "Deploy the same agent across dev, staging, and production without duplicating resources." (relevant to `ConvAIEnvVarLocator`)
- https://elevenlabs.io/docs/eleven-agents/customization/personalization/twilio-personalization.md — conversation-initiation webhook that returns dynamic variables server-side.
- https://elevenlabs.io/docs/eleven-agents/customization/tools/mcp.md and .../mcp/security.md
