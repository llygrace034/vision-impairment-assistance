# ElevenLabs Agents — "Custom LLM" contract (verified 2026-10-03)

Research note for **LetterLens**. Every claim below is traceable to a doc page fetched on
2026-10-03. Where a fact could **not** be confirmed from primary docs it is marked
**UNCONFIRMED** and the reasoning is shown separately from the evidence. Do not promote an
UNCONFIRMED item to a design assumption without testing it against a live agent.

## 0. Sources fetched (all retrieved 2026-10-03)

| # | URL | Notes |
|---|-----|-------|
| S1 | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm.md | **Primary page. Resolves 200 — no 404, no rename problem.** 30,036 bytes / 836 lines |
| S2 | https://elevenlabs.io/docs/llms.txt | Doc index, 215,130 bytes |
| S3 | https://elevenlabs.io/docs/api-reference/agents/create.md | Create-agent API ref; contains the `CustomLLM` schema |
| S4 | https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools.md | System tools + "Custom LLM integration" section |
| S5 | https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools.md | Client tool config shape |
| S6 | https://elevenlabs.io/docs/eleven-agents/customization/tools.md | Tool taxonomy |
| S7 | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm/groq-cloud.md | Server-URL convention evidence |
| S8 | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm/cloudflare.md | Server-URL convention evidence |
| S9 | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm/together-ai.md | Server-URL convention evidence |
| S10 | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm/samba-nova-cloud.md | Server-URL convention evidence |
| S11 | https://elevenlabs.io/docs/eleven-agents/customization/llm/llm-cascading.md | Retry behaviour for custom LLMs |
| S12 | https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow.md | Soft timeout / turn timeout |
| S13 | https://elevenlabs.io/docs/eleven-agents/phone-numbers/twilio-integration/custom-llm-integration.md | **Different feature** — Speech Engine WebSocket "brain", not the HTTP custom LLM |
| S14 | https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml | Official OpenAI OpenAPI spec (primary) — used for chunk/tool-call delta shapes that ElevenLabs delegates to |

### Naming / URL status

The product **has** been renamed to "ElevenLabs Agents" and the live doc tree is
`/docs/eleven-agents/...`. `https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm.md`
returns 200. The old `/docs/conversational-ai/...` and `/docs/agents-platform/...` paths still appear
in search results and redirect, but **use `/docs/eleven-agents/...` as canonical**. Note the doc page
title is "Integrate your own model", and the in-page anchor for sub-pages is
`/docs/eleven-agents/customization/llm/custom-llm/<provider>`.

> Caution: `https://elevenlabs.io/docs/llms-full.txt` is advertised on every page but currently
> returns a byte-identical copy of `llms.txt` (215,130 bytes). It is **not** a full-corpus dump.
> Fetch individual `.md` pages instead.

Also note: `WebFetch` against these pages returns an LLM *summary*, not the page. To get verbatim
markdown use `curl -sSL <url>.md`. All quotes below came from curl.

---

## 1. Overview — two supported API shapes

Verbatim (S1):

> By default, we use our own internal credentials for popular models like OpenAI. To use a custom LLM server, it must align with one of the following OpenAI-compatible request/response structures:
>
> * [Chat Completions API](https://platform.openai.com/docs/api-reference/chat/create) (`/v1/chat/completions`)
> * [Responses API](https://platform.openai.com/docs/api-reference/responses/create) (`/v1/responses`)

And:

> The Responses API is OpenAI's newer API format that supports additional features. Both API formats are fully supported for custom LLM integration.

The API reference (S3) exposes this as a third option too — `api_type` has **three** allowed values:

```
- `api_type` (enum, optional, default: chat_completions) — The API type to use (chat_completions, responses or websocket)
  - Allowed values: `chat_completions`, `responses`, `websocket`
```

`websocket` is the Speech Engine "brain WebSocket" path (S13), a genuinely different architecture —
ElevenLabs connects **out** to your WebSocket and sends transcripts rather than OpenAI messages. For
LetterLens, **`chat_completions` (the default) is the one to build.**

---

## 2. The exact HTTP contract

### 2.1 Method and path convention

**Method: `POST`.** (Every server example in S1 is `@app.post("/v1/chat/completions")` /
`app.post("/v1/chat/completions", ...)`.)

**Path: ElevenLabs appends the path. You configure a BASE url.** This is the single most important
operational fact and it is *not* stated in one sentence anywhere — it is established by four
provider guides that all tell you to paste a base URL ending in `/v1`:

| Source | Configured "Server URL" | Provider's own curl endpoint |
|---|---|---|
| S7 Groq | `https://api.groq.com/openai/v1` | `https://api.groq.com/openai/v1/chat/completions` |
| S9 Together AI | `https://api.together.xyz/v1` | `https://api.together.xyz/v1/chat/completions` |
| S10 SambaNova | `https://api.sambanova.ai/v1` | `https://api.sambanova.ai/v1/chat/completions` |
| S8 Cloudflare | `https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1/` | `https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/v1/chat/completions` |

Verbatim (S7):

> For the Server URL, specify Groq's OpenAI-compatible API endpoint: `https://api.groq.com/openai/v1`. For the Model ID, specify `meta-llama/llama-4-scout-17b-16e-instruct` as discussed above, and select your API key from the dropdown menu.

Verbatim (S9):

> For the Server URL, specify Together AI's OpenAI-compatible API endpoint: `https://api.together.xyz/v1`.

**Conflicting wording to be aware of.** The API reference (S3) describes the field as the *full*
endpoint:

```
### CustomLLM

- `url` (string, required) — The URL of the Chat Completions compatible endpoint
```

Note Cloudflare's example has a **trailing slash** (`/ai/v1/`) while Groq/Together/SambaNova do not,
and both are presented as working. That implies ElevenLabs normalises the join.

**Build recommendation for LetterLens:** host the proxy so that **both** work. Mount the handler at
`POST /v1/chat/completions` and configure the dashboard Server URL as the base
(`https://<host>/v1`). Additionally register a catch-all `POST /v1/chat/completions/chat/completions`
→ same handler (or a path-normalising middleware), so a double-append or a full-URL paste cannot take
the agent down. This is cheap insurance against an undocumented join rule.

### 2.2 Required response transport

Verbatim (S1):

> Both endpoints must return responses in SSE (Server-Sent Events) format with `Content-Type: text/event-stream`.

For Chat Completions specifically, verbatim (S1):

> The Chat Completions API uses the `/v1/chat/completions` endpoint.
>
> Each chunk must be formatted as `data: {json}\n\n` and the stream must end with `data: [DONE]\n\n`.

So, confirmed:

- `Content-Type: text/event-stream`
- framing: `data: ` + compact JSON + `\n\n`
- **terminating sentinel: `data: [DONE]\n\n`** — yes, `[DONE]`, and it is sent as a `data:` line like
  any other chunk (not a bare `[DONE]`, not an `event: done`).

The TypeScript example in S1 sets these three headers:

```typescript
res.setHeader("Content-Type", "text/event-stream");
res.setHeader("Cache-Control", "no-cache");
res.setHeader("Connection", "keep-alive");
```

For the Responses API variant (not our path, recorded for completeness), verbatim (S1):

> Each chunk must be formatted as `event: {type}\ndata: {json}\n\n` and the stream must end with `data: [DONE]\n\n`. The minimum required events are:
>
> * `response.output_text.delta` - for streaming text content
> * `response.completed` - to signal completion

### 2.3 Reference server implementation (verbatim, S1)

```python
import json
import os
import fastapi
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import uvicorn
import logging
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

app = fastapi.FastAPI()
oai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    user_id: Optional[str] = None

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest) -> StreamingResponse:
    oai_request = request.dict(exclude_none=True)
    if "user_id" in oai_request:
        oai_request["user"] = oai_request.pop("user_id")

    chat_completion_coroutine = await oai_client.chat.completions.create(**oai_request)

    async def event_stream():
        try:
            async for chunk in chat_completion_coroutine:
                # Convert the ChatCompletionChunk to a dictionary before JSON serialization
                chunk_dict = chunk.model_dump()
                yield f"data: {json.dumps(chunk_dict)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logging.error("An error occurred: %s", str(e))
            yield f"data: {json.dumps({'error': 'Internal error occurred!'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8013)
```

**Two things to extract from this example beyond the obvious:**

1. **ElevenLabs sends `user_id`, not OpenAI's `user`.** The request model declares
   `user_id: Optional[str] = None` and the handler *renames* it before forwarding upstream:
   `oai_request["user"] = oai_request.pop("user_id")`. This rename appears in every variant of the
   example in S1 (plain, buffer-words, and extra-params versions) and in the TypeScript version
   (`oaiRequest.user = oaiRequest.user_id; delete oaiRequest.user_id;`). A strict OpenAI-schema proxy
   would reject this field. Confidence: **high** that the field name is `user_id`; **medium** on
   whether it is always present.
2. **The error path is an SSE `data:` line, not an HTTP error.** Once the stream has opened, the
   example emits `data: {"error": "Internal error occurred!"}\n\n`. ElevenLabs' documented example
   notably does **not** send `[DONE]` on the error path.

### 2.4 Error handling

There is **no documented error contract** — no documented status codes, no documented error envelope
that ElevenLabs parses. The only evidence is the example above (an `{"error": "..."}` object pushed
as an SSE data frame). Treat the shape of an error ElevenLabs *understands* as **UNCONFIRMED**. What
*is* documented is what happens next: see §6 retries.

---

## 3. Authentication to the custom LLM server

### 3.1 Dashboard flow (verbatim, S1)

> To integrate a custom OpenAI key, update your agent settings in the ElevenLabs dashboard to point to your custom LLM server and create a secret containing your `OPENAI_API_KEY`:
>
> In your Agent settings in the ElevenLabs dashboard, select "Custom LLM" from the "LLM" dropdown menu on the right.
>
> Click on the field under "LLM" and scroll down to select "Custom LLM".
>
> Enter the server URL and the Model ID of your custom LLM server.
>
> Click the dropdown under "API key" and select "Create new secret". Name the key `OPENAI_API_KEY` and add the key to the "value" field and click "Add secret".
>
> Click the "x" button to close the LLM modal and click "Publish" to save your changes.

Note `OPENAI_API_KEY` is the *secret name* used in that walkthrough, not a required name — S10 has
the user select a secret named `SAMBANOVA_API_KEY`.

### 3.2 The API-level schema (verbatim, S3)

```
### CustomLLM

- `url` (string, required) — The URL of the Chat Completions compatible endpoint
- `model_id` (string, optional, nullable) — The model ID to be used if URL serves multiple models
- `api_key` (CustomLlmApiKey, optional, nullable) — The API key for authentication. Either a workspace secret reference {'secret_id': '...'} or an environment variable reference {'env_var_label': '...'}.
- `auth_connection` (CustomLlmAuthConnection, optional, nullable) — Optional workspace auth connection for authentication. Only auth connections that produce an Authorization Bearer token are supported; Basic auth, mTLS, custom header, and URL secret auth connections are not supported.
- `request_headers` (map from string to CustomLlmRequestHeaders, optional) — Headers that should be included in the request
- `api_version` (string, optional, nullable) — The API version to use for the request
- `api_type` (enum, optional, default: chat_completions) — The API type to use (chat_completions, responses or websocket)
  - Allowed values: `chat_completions`, `responses`, `websocket`
```

### 3.3 Which header carries the key?

**The header name is never stated verbatim in ElevenLabs' docs. Confidence: medium (inferred).**
The evidence that it is `Authorization: Bearer <key>`:

- The `auth_connection` description says: *"Only auth connections that produce an **Authorization
  Bearer token** are supported; Basic auth, mTLS, custom header, and URL secret auth connections are
  not supported."* (S3) — that is ElevenLabs stating its own outbound auth mechanism for custom LLM.
- All four provider guides have you paste a provider key into the same "API key" dropdown, and all
  four providers accept **only** `Authorization: Bearer`:
  - S7 Groq: `-H "Authorization: Bearer $GROQ_API_KEY"`
  - S8 Cloudflare: `-H "Authorization: Bearer {API_TOKEN}"`
  - S9 Together: `-H "Authorization: Bearer <API_KEY>"`
  - S10 SambaNova: `curl -H "Authorization: Bearer <your-api-key>"`

  If ElevenLabs sent any other header name, none of these four documented integrations could work.

**For LetterLens:** validate `Authorization: Bearer <shared secret>` on the proxy, but **accept a
fallback** and log the full inbound header set on the first request so you can confirm empirically.
If you need a non-standard header, use **`request_headers`** — it is the documented, supported escape
hatch ("Headers that should be included in the request") and it does not go through
`auth_connection`'s Bearer-only restriction.

> **Security note:** the custom LLM URL is effectively an open endpoint on the internet (S1
> recommends `ngrok http --url=<Your url>.ngrok.app 8013` to expose it). Auth is *your*
> responsibility — nothing in the contract authenticates ElevenLabs to you beyond the key you
> configure.

---

## 4. `elevenlabs_extra_body` and non-OpenAI fields

### 4.1 What it is

A field ElevenLabs injects into the request body carrying arbitrary caller-supplied key/values from
the client SDK's conversation-initiation data. Verbatim (S1), under "Custom LLM Parameters":

> You may pass additional parameters to your custom LLM implementation.

Client side (verbatim, S1):

```python
from elevenlabs.conversational_ai.conversation import Conversation, ConversationInitiationData

extra_body_for_convai = {
    "UUID": "123e4567-e89b-12d3-a456-426614174000",
    "parameter-1": "value-1",
    "parameter-2": "value-2",
}

config = ConversationInitiationData(
    extra_body=extra_body_for_convai,
)
```

Note the asymmetry: the **client SDK** field is `extra_body`; the field that lands in the **HTTP
request body** to your server is `elevenlabs_extra_body`.

### 4.2 It must be enabled server-side first

From the Create-agent reference (S3), under `ConversationInitiationClientDataConfig-Input`:

```
- `custom_llm_extra_body` (boolean, optional, default: false) — Whether to include custom LLM extra body
```

**Default is `false`.** If LetterLens relies on `elevenlabs_extra_body` to route per-letter context,
this flag must be flipped on the agent
(`platform_settings.overrides.conversation_initiation_client_data_config.custom_llm_extra_body = true`
— exact nesting **UNCONFIRMED**, the ref only names the object type) or the field will silently never
arrive. This is a classic silent-failure trap.

### 4.3 The verbatim request body ElevenLabs sends

This is the only full request example in the docs (S1, "Example Request"):

```json
{
  "messages": [
    {
      "role": "system",
      "content": "\n  <Redacted>"
    },
    {
      "role": "assistant",
      "content": "Hey I'm currently unavailable."
    },
    {
      "role": "user",
      "content": "Hey, who are you?"
    }
  ],
  "model": "gpt-4o",
  "temperature": 0.5,
  "max_tokens": 5000,
  "stream": true,
  "elevenlabs_extra_body": {
    "UUID": "123e4567-e89b-12d3-a456-426614174000",
    "parameter-1": "value-1",
    "parameter-2": "value-2"
  }
}
```

Observations that matter for the build:

- `"stream": true` — ElevenLabs always streams. There is **no documented non-streaming mode**.
- The **system prompt arrives as `messages[0]` with `role: "system"`** (shown redacted). ElevenLabs
  builds it from the agent's prompt, personality, tool instructions, knowledge-base/RAG chunks and
  dynamic variables. Your proxy will receive a large system message it did not author.
- The agent's **first message** arrives as a `role: "assistant"` turn, i.e. conversation history is
  pre-seeded. Your proxy must not assume `messages[-1].role == "user"` on the first call.
- `max_tokens` is present and corresponds to the dashboard's "Limit token usage" setting — S1:
  *"Direct your server URL to ngrok endpoint and set 'Limit token usage' to 5000."*
- `model` is the **Model ID string you typed in the dashboard**, echoed into the body verbatim. For a
  self-hosted proxy you can put anything there (e.g. `letterlens-v1`) and switch on it.

### 4.4 Recommended proxy handling of unknown fields

The docs' own pattern is **strip-then-forward**. Verbatim (S1), the extra-params server variant:

```python
class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    user_id: Optional[str] = None
    elevenlabs_extra_body: Optional[dict] = None

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest) -> StreamingResponse:
    oai_request = request.dict(exclude_none=True)
    print(oai_request)
    if "user_id" in oai_request:
        oai_request["user"] = oai_request.pop("user_id")

    if "elevenlabs_extra_body" in oai_request:
        oai_request.pop("elevenlabs_extra_body")

    chat_completion_coroutine = await oai_client.chat.completions.create(**oai_request)
```

So: **declare it, read it, then `pop()` it before forwarding upstream.** Pydantic's default
behaviour (ignore undeclared keys) is what makes this safe — the model does not use
`extra="forbid"`. For LetterLens:

- Model the request with **`extra="allow"` (or `extra="ignore"`)** — never `extra="forbid"`.
  ElevenLabs has already added `user_id` and `elevenlabs_extra_body` beyond the OpenAI spec and may
  add more (`enable_reasoning_summary` / `reasoning.summary` are already referenced, see §7).
- Maintain an **explicit allowlist** of keys forwarded to the upstream model provider; drop
  everything else rather than passing unknown keys through (upstream providers *do* use
  `extra="forbid"` semantics and will 400).
- Log unrecognised top-level keys at WARN once per key so contract drift is visible.

---

## 5. Tools

### 5.1 System tools ARE passed as OpenAI `tools` entries — confirmed

Verbatim (S1):

> Your custom LLM can trigger [system tools](/docs/eleven-agents/customization/tools/system-tools) to control conversation flow and state. **These tools are automatically included in the `tools` parameter of your chat completion requests when configured in your agent.**

And the loop, verbatim (S1):

> 1. **LLM Decision**: Your custom LLM decides when to call these tools based on conversation context
> 2. **Tool Response**: The LLM responds with function calls in standard OpenAI format
> 3. **Backend Processing**: ElevenLabs processes the tool calls and updates conversation state

Plus the hard requirement, verbatim (S1):

> Your custom LLM must support function calling to use system tools. Ensure your model can generate proper function call responses in OpenAI format.

S4 confirms independently: *"When using a custom LLM with ElevenLabs agents, system tools are exposed
as function definitions that your LLM can call."*

### 5.2 Exact declared system tool names

Confirmed names (note #3 and #4 — the names do **not** match the doc headings):

| Doc heading | **Declared function name** | Required params | Optional params |
|---|---|---|---|
| End call | `end_call` | `reason` (string) | `message` (string) |
| Language detection | `language_detection` | `reason`, `language` (string) | — |
| Agent transfer | `transfer_to_agent` | `agent_number` (integer) | `reason` (string) |
| Transfer to human | **`transfer_to_number`** | `transfer_number` (string), `client_message` (string), `agent_message` (string) | `reason` (string) |
| Skip turn | `skip_turn` | — | `reason` (string) |
| Voicemail detection | `voicemail_detection` | `reason` (string) | — |

Beware the mismatch: the section is titled **"Transfer to human"** but the function is
**`transfer_to_number`**. Do not hardcode `transfer_to_human`.

Two further system tools exist in the API ref `BuiltInTools-Input` (S3) and in llms.txt (S2) but have
**no documented custom-LLM function schema**: `play_keypad_touch_tone` ("The play DTMF tool"),
`update_state`, and `flag_issue_for_review`. Their function names and argument schemas are
**UNCONFIRMED** for the custom-LLM path.

`BuiltInTools-Input` verbatim (S3):

```
- `end_call` (SystemToolConfig, optional, nullable) — The end call tool
- `language_detection` (SystemToolConfig, optional, nullable) — The language detection tool
- `transfer_to_number` (SystemToolConfig, optional, nullable) — The transfer to number tool
- `skip_turn` (SystemToolConfig, optional, nullable) — The skip turn tool
- `play_keypad_touch_tone` (SystemToolConfig, optional, nullable) — The play DTMF tool
- `voicemail_detection` (SystemToolConfig, optional, nullable) — The voicemail detection tool
```

### 5.3 Verbatim system-tool function-call formats (S1)

These are shown as **non-streaming** `{type, function}` objects — see §5.6 for the streaming caveat.

```json
{
  "type": "function",
  "function": {
    "name": "end_call",
    "arguments": "{\"reason\": \"Task completed successfully\", \"message\": \"Thank you for using our service. Have a great day!\"}"
  }
}
```

```json
{
  "type": "function",
  "function": {
    "name": "language_detection",
    "arguments": "{\"reason\": \"User requested Spanish\", \"language\": \"es\"}"
  }
}
```

```json
{
  "type": "function",
  "function": {
    "name": "transfer_to_agent",
    "arguments": "{\"reason\": \"User needs billing support\", \"agent_number\": 0}"
  }
}
```

```json
{
  "type": "function",
  "function": {
    "name": "transfer_to_number",
    "arguments": "{\"reason\": \"Complex billing issue\", \"transfer_number\": \"+15551234567\", \"client_message\": \"I'm transferring you to a billing specialist who can help with your account.\", \"agent_message\": \"Customer has a complex billing dispute about order #12345 from last month.\"}"
  }
}
```

```json
{
  "type": "function",
  "function": {
    "name": "skip_turn",
    "arguments": "{\"reason\": \"User requested time to think\"}"
  }
}
```

```json
{
  "type": "function",
  "function": {
    "name": "voicemail_detection",
    "arguments": "{\"reason\": \"Automated greeting detected with request to leave message\"}"
  }
}
```

### 5.4 Verbatim example request WITH tools (S1)

This is the authoritative example of what the `tools` array looks like on the wire. **Note the
declared JSON Schemas** — and note that the `description` strings are truncated with `...` in the
docs, so the real system prompt injection is longer.

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant. You have access to system tools for managing conversations."
    },
    {
      "role": "user",
      "content": "I think we're done here, thanks for your help!"
    }
  ],
  "model": "your-custom-model",
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": true,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "end_call",
        "description": "Call this function to end the current conversation when the main task has been completed...",
        "parameters": {
          "type": "object",
          "properties": {
            "reason": {
              "type": "string",
              "description": "The reason for the tool call."
            },
            "message": {
              "type": "string",
              "description": "A farewell message to send to the user along right before ending the call."
            }
          },
          "required": ["reason"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "language_detection",
        "description": "Change the conversation language when the user expresses a language preference explicitly...",
        "parameters": {
          "type": "object",
          "properties": {
            "reason": {
              "type": "string",
              "description": "The reason for the tool call."
            },
            "language": {
              "type": "string",
              "description": "The language to switch to. Must be one of language codes in tool description."
            }
          },
          "required": ["reason", "language"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "skip_turn",
        "description": "Skip a turn when the user explicitly indicates they need a moment to think...",
        "parameters": {
          "type": "object",
          "properties": {
            "reason": {
              "type": "string",
              "description": "Optional free-form reason explaining why the pause is needed."
            }
          },
          "required": []
        }
      }
    }
  ]
}
```

### 5.5 Server tools vs client tools in the `tools` array — **NOT DOCUMENTED. This is the main gap.**

**Answer: UNCONFIRMED. Confidence: low on the documentation; medium-high on the inference.**

The docs say *only* that **system** tools are auto-included in `tools` (S1, quoted in §5.1). I
searched S1, S4, S5, S6, the webhook-tools page, the client-tools page, and llms.txt and found **no
statement either way** about webhook (server) tools or client tools being included in the custom
LLM's `tools` array, and no statement that ElevenLabs handles them out-of-band. There is no verbatim
quote to give you, because there is no sentence to quote. **Do not let anyone put a confident quote
here.**

ElevenLabs' tool taxonomy, verbatim (S6):

> ElevenLabs Agents supports the following kinds of tools:
>
> #### [Client Tools](/docs/eleven-agents/customization/tools/client-tools)
> Tools executed directly on the client-side application (e.g., web browser, mobile app).
>
> #### [Webhook tools](/docs/eleven-agents/customization/tools/webhook-tools)
> Custom tools that call external APIs through webhooks.
>
> #### [Code Tools](/docs/eleven-agents/customization/tools/code-tools)
> Custom JavaScript executed in a sandboxed environment on ElevenLabs' infrastructure.
>
> #### [MCP Tools](/docs/eleven-agents/customization/tools/mcp)
> Model Context Protocol servers that provide tools and resources to agents.
>
> #### [System Tools](/docs/eleven-agents/customization/tools/system-tools)
> Built-in tools provided by the platform for common actions.

**The architectural inference (reasoning, not evidence).** All five tool kinds are *executed* by
somebody other than the LLM (ElevenLabs' backend for webhook/code/MCP, the client app for client
tools, ElevenLabs' state machine for system tools), but in all five cases the **decision** to invoke
is the LLM's — that is what a tool is. With a custom LLM, ElevenLabs has no other model in the loop
to make that decision. Therefore webhook, code, MCP and client tools **must** be declared in the
`tools` array sent to your server, and your server must relay the resulting `tool_calls` back for
ElevenLabs to execute. Corroborating hints:

- S7 (Groq): *"To make use of the full power of ElevenLabs agents you need to use a model that
  supports tool use and structured outputs."* — stated as a general requirement for agents, not
  specifically system tools.
- S13 describes the WebSocket brain as the option for *"function-call routing"* on your own server,
  implying the HTTP custom-LLM path routes function calls through ElevenLabs instead.
- Client tools are declared with a JSON Schema `parameters` block identical in shape to an OpenAI
  function (S5), which only makes sense if it is serialised into a `tools` entry:

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

  Note `"type": "client"` in ElevenLabs' own tool config — this is **not** the OpenAI `"type":
  "function"`, so ElevenLabs is doing a translation step somewhere.

**Required action before building:** attach one webhook tool and one client tool to a throwaway
agent, point it at a proxy that does nothing but `print(request_body)`, and record the actual `tools`
array. **This one experiment resolves the whole architectural question in five minutes and should be
step 1 of implementation.** Until then, write the proxy to pass `tools` through untouched and relay
all `tool_calls` verbatim — that behaviour is correct under *either* answer.

### 5.6 The streamed TOOL CALL delta shape — ElevenLabs does not document it

**ElevenLabs shows only the non-streaming `{type, function}` form (§5.3). The streaming
`delta.tool_calls` shape with `index`/`id`/fragmented `arguments` is NOT documented by ElevenLabs.**
Confidence in the shape itself: **high**, but sourced from OpenAI's spec (S14), which ElevenLabs
delegates to ("it must align with one of the following OpenAI-compatible request/response
structures", S1) and which its own example reproduces by dumping the OpenAI SDK's `ChatCompletionChunk`
(`chunk.model_dump()`).

From the official OpenAI OpenAPI spec (S14), `ChatCompletionStreamResponseDelta`:

```yaml
    ChatCompletionStreamResponseDelta:
      type: object
      description: A chat completion delta generated by streamed model responses.
      properties:
        content:
          anyOf:
            - type: string
              description: The contents of the chunk message.
            - type: "null"
        tool_calls:
          type: array
          items:
            $ref: "#/components/schemas/ChatCompletionMessageToolCallChunk"
        role:
          type: string
          enum:
            - developer
            - system
            - user
            - assistant
            - tool
        refusal:
          anyOf:
            - type: string
            - type: "null"
```

And `ChatCompletionMessageToolCallChunk` (S14) — note **`index` is the only required field**:

```yaml
    ChatCompletionMessageToolCallChunk:
      type: object
      properties:
        index:
          type: integer
        id:
          type: string
          description: The ID of the tool call.
        type:
          type: string
          enum:
            - function
          description: The type of the tool. Currently, only `function` is supported.
        function:
          type: object
          properties:
            name:
              type: string
              description: The name of the function to call.
            arguments:
              type: string
              description: The arguments to call the function with, as generated by the model
                in JSON format. Note that the model does not always generate
                valid JSON, and may hallucinate parameters not defined by your
                function schema. Validate the arguments in your code before
                calling your function.
      required:
        - index
```

So a tool call streams as: a **first** chunk carrying `index`, `id`, `type: "function"` and
`function.name`, then **N** chunks carrying only `index` and `function.arguments` fragments that the
receiver concatenates, then a chunk with `finish_reason: "tool_calls"`. Concretely (constructed from
the S14 schema, **not** a verbatim doc example — label as such):

```
data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1759449600,"model":"letterlens-v1","choices":[{"index":0,"delta":{"role":"assistant","content":null,"tool_calls":[{"index":0,"id":"call_abc123","type":"function","function":{"name":"end_call","arguments":""}}]},"finish_reason":null}]}

data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1759449600,"model":"letterlens-v1","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"reason\":\""}}]},"finish_reason":null}]}

data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1759449600,"model":"letterlens-v1","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"done\"}"}}]},"finish_reason":null}]}

data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1759449600,"model":"letterlens-v1","choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}]}

data: [DONE]
```

**Whether ElevenLabs' parser tolerates emitting a tool call as a single un-fragmented chunk (all of
`id` + `name` + complete `arguments` in one delta) is UNCONFIRMED.** It almost certainly does, since
that is a legal stream, and emitting one consolidated chunk is the safer thing for a proxy to do
anyway — it removes any chance of ElevenLabs mis-reassembling fragments. **Recommendation: buffer
tool-call fragments in the proxy and emit one complete tool-call chunk.** Test it.

---

## 6. Timeouts and retries

**There is no documented timeout for first token or full response from a custom LLM.** Confidence:
**high** that it is undocumented (searched S1, S2, S3, S11, S12 and web search scoped to
elevenlabs.io); the actual server-side value is **UNCONFIRMED**. Do not design to a guessed number.

What *is* documented and adjacent:

**`cascade_timeout_seconds`** (S3) — the closest thing to a first-token budget:

```
- `cascade_timeout_seconds` (double, optional, default: 4) — Time in seconds before cascading to backup LLM. Must be between 2 and 15 seconds.
```

**But for a custom LLM, cascading is disabled.** Verbatim (S11):

> When you configure a [Custom LLM](/docs/eleven-agents/customization/llm/custom-llm), the standard cascading logic to *other* models is bypassed. The system will attempt to use your specified Custom LLM.
>
> If your Custom LLM fails, the system will retry the request with the *same* Custom LLM multiple times (matching the standard minimum retry count) before considering the request failed. It will not fall back to ElevenLabs-hosted models, ensuring your specific configuration is respected.

The "standard minimum retry count" is defined in S11 as:

> **Retries:** The system retries the generation process multiple times (at least 3 attempts) across the sequence of available LLMs (preferred + backups).

So: **at least 3 attempts against your server.** Verbatim on what counts as failure (S11):

> Failures can include API errors, timeouts, or empty responses from the LLM provider.

**Implication for LetterLens: your proxy must be idempotent-safe under retry.** A slow or erroring
response produces ≥3 duplicate POSTs for one user turn. If the proxy has side effects (writing a
record, sending mail, charging anything), key them on something stable and dedupe. Drop a
request-level idempotency key into `elevenlabs_extra_body` if you can, or hash
`(conversation_id, len(messages), last_user_message)`.

**`soft_timeout_config`** (S3, S12) — not a timeout *on* you, but it determines what the caller hears
while you are slow:

```
### SoftTimeoutConfig

Configuration for soft timeout functionality during LLM response generation.

- `timeout_seconds` (double, optional, default: -1) — Time in seconds before showing the predefined message while waiting for LLM response. Set to -1 to disable.
- `message` (string, optional, default: Hhmmmm...yeah.) — Message to show when the first soft timeout is reached while waiting for LLM response. Supports dynamic variables (e.g., {{system__time}}, {{custom_variable}}).
- `additional_soft_timeout_messages` (list of string, optional) — Extra static filler messages for subsequent soft timeouts in the same LLM generation. The first timeout uses `message`. If fewer messages are configured than `max_soft_timeouts_per_generation`, the last configured message is repeated; otherwise a built-in filler is used.
- `use_llm_generated_message` (boolean, optional, default: false) — If enabled, the soft timeout message will be generated dynamically instead of using the static message.
- `randomize_fillers` (boolean, optional, default: false) — If enabled, shuffle the order of static soft timeout messages once at the start of each turn. Only applies when use_llm_generated_message is false.
- `max_soft_timeouts_per_generation` (integer, optional, default: 1) — Maximum filler messages while waiting for a single LLM response. Fires every timeout_seconds until the LLM streams content or this limit is reached.
- `disable_until_first_user_message` (boolean, optional, default: false) — When true, soft timeout fillers are suppressed until the conversation has at least one real user message.
```

Verbatim mechanism (S12):

> 1. When the user finishes speaking, the system starts generating an LLM response
> 2. A timer begins based on the configured timeout duration
> 3. If the LLM response arrives **before** the timeout, no filler is spoken
> 4. If the timeout is reached **before** the LLM responds:
>    * The configured filler message is spoken immediately
>    * The agent continues waiting for the actual response
>    * Once ready, the agent speaks the full LLM response

Note "Fires every `timeout_seconds` until **the LLM streams content**" — confirming ElevenLabs
measures **time to first streamed content**, which is the latency metric that matters.

**Buffer words — ElevenLabs' own recommended mitigation for a slow custom LLM.** Verbatim (S1):

> If your custom LLM has slow processing times (perhaps due to agentic reasoning or pre-processing requirements) you can improve the conversational flow by implementing **buffer words** in your streaming responses.
>
> When your LLM needs more time to process the full response, return an initial response ending with `"... "` (ellipsis followed by a space). This allows the Text to Speech system to maintain natural flow while keeping the conversation feeling dynamic.
> This creates natural pauses that flow well into subsequent content that the LLM can reason longer about. The extra space is crucial to ensure that the subsequent content is not appended to the "..." which can lead to audio distortions.

The trailing space is a real requirement, not a typo. The documented buffer chunk (verbatim, S1):

```python
            initial_chunk = {
                "id": "chatcmpl-buffer",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": request.model,
                "choices": [{
                    "delta": {"content": "Let me think about that... "},
                    "index": 0,
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(initial_chunk)}\n\n"
```

Other timeouts, for completeness — these bound the *conversation*, not your response:

- `turn_timeout` (default 7s, range 1–30) — "Maximum wait time for the user's reply before re-engaging the user" (S3)
- `silence_end_call_timeout` (default -1) — "Maximum wait time since the user last spoke before terminating the call" (S3)
- Max conversation duration: *"The default is 600 seconds (10 minutes). You can set a value from 60 to 7,200 seconds."* (S12)

---

## 7. Chunk envelope requirements: `id`, `object`, `model`, `finish_reason`, `usage`

ElevenLabs never states these requirements directly. The strongest ElevenLabs-side evidence is its
**own hand-rolled buffer chunk** (§6), which includes `id`, `object: "chat.completion.chunk"`,
`created`, `model` and `choices[0].{delta,index,finish_reason}`. Since ElevenLabs wrote that chunk by
hand rather than via the SDK, treat every field in it as **required in practice**. Confidence:
**medium-high**.

The normative shape comes from the OpenAI spec (S14), `CreateChatCompletionStreamResponse`:

```yaml
      required:
        - choices
        - created
        - id
        - model
        - object
```

Per-choice (S14):

```yaml
          items:
            type: object
            required:
              - delta
              - finish_reason
              - index
```

Field-by-field (descriptions verbatim from S14):

- **`id`** — *"A unique identifier for the chat completion. Each chunk has the same ID."* Required.
  ElevenLabs' buffer example uses the literal `"chatcmpl-buffer"`, i.e. a **different** id from the
  chunks that follow it. So ElevenLabs is demonstrably tolerant of a changing `id` mid-stream, and
  does not appear to key on it.
- **`object`** — *"The object type, which is always `chat.completion.chunk`."* Required, enum of one
  value. **Always emit `"object": "chat.completion.chunk"`.**
- **`created`** — *"The Unix timestamp (in seconds) of when the chat completion was created. Each
  chunk has the same timestamp."* Required. (ElevenLabs' example hardcodes `1234567890`.)
- **`model`** — *"The model to generate the completion."* Required. **Echo it back.** ElevenLabs'
  example uses `request.model` / `model: request.model`, i.e. echoes the inbound value. Whether
  ElevenLabs *validates* the echoed value against the configured Model ID is **UNCONFIRMED** —
  echoing it is free, so echo it.
- **`choices[].index`** — required; `0` for a single completion.
- **`choices[].finish_reason`** — required per the OpenAI schema (nullable), enum
  `stop | length | tool_calls | content_filter | function_call | null`. **Whether ElevenLabs requires
  a final chunk carrying a non-null `finish_reason` is UNCONFIRMED** — its own examples set
  `finish_reason: None` on the buffer chunk and rely on the upstream SDK for the rest, and the only
  documented stream terminator is `data: [DONE]`. OpenAI's reference final chunk (verbatim, S14):

  ```
  data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-6-astra", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{},"logprobs":null,"finish_reason":"stop"}]}
  ```

  **Recommendation: always emit it** — `"stop"` for text, `"tool_calls"` when the turn ends in a tool
  call — immediately before `data: [DONE]\n\n`. It costs nothing and `tool_calls` is the standard
  signal that a tool call is complete.
- **`usage`** — **not required.** Verbatim (S14): *"An optional field that will only be present when
  you set `stream_options: {"include_usage": true}` in your request."* ElevenLabs' documented request
  bodies (§4.3, §5.4) contain **no `stream_options`**, so ElevenLabs is not asking for usage.
  **No usage reporting is required of a custom LLM.** Nothing in S1/S3 suggests ElevenLabs reads
  token usage from a custom LLM response; billing-visible token counts for a custom LLM are
  **UNCONFIRMED**. Emitting a final usage chunk is harmless but `choices` would be `[]` on it, which
  a strict consumer might not expect — **safer to omit it**.
- **`logprobs`** — required-with-`delta` only inside OpenAI's own schema when present; set `null`.
- **`system_fingerprint`** — marked `deprecated: true` in S14. Omit.
- **`obfuscation`** — a newer OpenAI field (*"An obfuscation string added to normalize the size of
  streamed chunks as a mitigation to certain side-channel attacks"*). Irrelevant here; omit.

### Reasoning summary (relevant if LetterLens uses a reasoning model)

Verbatim (S1):

> Your endpoint must return reasoning separately from the final answer. ElevenLabs does not generate reasoning from the final answer.
>
> To request reasoning from a supported endpoint, turn on **Reasoning summary** in the agent's LLM settings or set `enable_reasoning_summary` via the API.

> #### Chat Completions API
>
> Stream reasoning in the `reasoning` or `reasoning_content` field of each response delta.
>
> For Gemini-compatible endpoints, ElevenLabs requests thoughts with `google.thinking_config.include_thoughts` and reads content marked with `extra_content.google.thought`.

> #### Responses API
>
> Return a `reasoning` output item with the summary text in its `summary` field.
>
> With reasoning effort configured and Reasoning summary enabled, ElevenLabs sets `reasoning.summary` to `auto` in the request.

So on the Chat Completions path, reasoning rides in `choices[0].delta.reasoning` or
`choices[0].delta.reasoning_content` — **non-OpenAI-spec fields ElevenLabs reads.** Critically: if
your proxy puts reasoning into `delta.content`, **it will be spoken aloud to the caller.** Keep them
separate.

---

## 8. Build checklist for the LetterLens proxy

1. `POST /v1/chat/completions`; configure dashboard Server URL as the **base** (`https://<host>/v1`).
   Add a path-normalising middleware so a doubled `/chat/completions` still routes.
2. Validate `Authorization: Bearer <secret>`; use `request_headers` if a custom header is needed.
   **Log the full inbound header set on request #1** to confirm the header name empirically.
3. Parse the body with **`extra="allow"`**. Expect `messages`, `model`, `temperature`, `max_tokens`,
   `stream: true`, plus non-OpenAI `user_id` and `elevenlabs_extra_body`, plus `tools` when tools are
   configured. Strip `user_id` → `user` and `pop()` `elevenlabs_extra_body` before forwarding.
4. Do not assume `messages[-1].role == "user"` — the agent's first message arrives as an `assistant`
   turn and `messages[0]` is a large ElevenLabs-generated `system` prompt.
5. Respond `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`.
6. Emit every chunk as `data: <compact json>\n\n` with `id`, `object: "chat.completion.chunk"`,
   `created`, `model` (echoed), `choices[0].{index, delta, finish_reason}`.
7. Pass `tools` through untouched and relay `tool_calls` verbatim — correct under either answer to
   §5.5. Buffer tool-call argument fragments and emit one consolidated tool-call chunk.
8. Emit a final chunk with `finish_reason` (`"stop"` / `"tool_calls"`), then `data: [DONE]\n\n`.
9. Omit `usage` unless proven needed.
10. Make the handler **retry-safe** — ≥3 duplicate POSTs per turn on failure or timeout (§6).
11. Keep time-to-first-content low; use buffer words ending `"... "` (with the trailing space) if
    pre-processing is slow. Configure `soft_timeout_config.timeout_seconds` (default is `-1`,
    disabled) so callers get a filler instead of silence.
12. If using `elevenlabs_extra_body`, **set `custom_llm_extra_body: true` on the agent** — it
    defaults to `false` and fails silently otherwise.
13. Never put reasoning text in `delta.content`; use `delta.reasoning` / `delta.reasoning_content`.

## 9. Open questions to resolve by experiment (not by more reading)

| # | Question | How to settle it |
|---|---|---|
| Q1 | Are webhook/client/code/MCP tools in the `tools` array, or handled out-of-band? (**§5.5 — most important**) | Attach one webhook + one client tool to a throwaway agent, point at an echo proxy, dump the body. 5 minutes. |
| Q2 | Exact auth header name ElevenLabs sends | Log all inbound headers on request #1 of the same echo proxy. |
| Q3 | Does ElevenLabs append `/chat/completions`, and how does it treat a trailing slash or a full URL? | Echo proxy with a catch-all route; log `request.url.path`. |
| Q4 | First-token / total-response timeout | Echo proxy that sleeps N seconds before first chunk; bisect N. |
| Q5 | Is a non-null `finish_reason` chunk required before `[DONE]`? | Omit it once and see whether the turn completes. |
| Q6 | Is `user_id` always present, and does it carry a conversation or user identifier useful for idempotency? | Inspect echo-proxy output. |
| Q7 | Does a single consolidated tool-call chunk parse correctly? | Emit one; check the tool fires. |
| Q8 | Function names/schemas for `play_keypad_touch_tone`, `update_state`, `flag_issue_for_review` | Enable each and read the `tools` array from the echo proxy. |

**All eight are answered by one echo proxy.** Build that first.
