# 01 — Gemma models on the Gemini API

**Research dimension:** Which Gemma models actually exist on the Gemini API, and what can they do?
**Researched:** 2026-10-03
**Method:** live fetches of `ai.google.dev` primary docs (raw HTML → text) plus targeted web search. Every claim below is tagged with the URL it came from. Nothing here is from training-data memory.

---

## 0. HEADLINE ANSWER

**`gemma-4-26b-a4b-it` IS REAL.** The spec is not hallucinating. It is one of exactly two Gemma models served by the Gemini API, and "Gemma 4" is a real generation that shipped **2026-03-31**.

> "The Gemini API supports the following Gemma 4 models:
> gemma-4-31b-it
> gemma-4-26b-a4b-it"
> — https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api (page footer: *Last updated 2026-07-02 UTC*)

But there are three real traps the build must plan around, detailed in §8:

1. Gemma is **absent from the Gemini API model list page and from the rate-limits page entirely**. It is documented *only* on the Gemma microsite.
2. The Gemma page is written against the **legacy `:generateContent` surface**. The current Gemini API docs have moved to a new `POST /v1beta/interactions` API, and the `/gemini-api/docs/generate-content/*` pages are now titled "**Gemini Generate Content API (Legacy)**". No `interactions` doc page mentions Gemma.
3. **Structured output (`responseFormat` / `responseSchema` / `responseMimeType: application/json`) and streaming (`streamGenerateContent`) are NOT documented anywhere for Gemma.** They are not documented as unsupported either — they are simply absent. Treat both as unverified.

---

## 1. Every Gemma model ID on the Gemini API (verbatim)

Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api

Verbatim from the "Supported Models" section:

```
Supported Models

The Gemini API supports the following Gemma 4 models:

gemma-4-31b-it

gemma-4-26b-a4b-it
```

That is the **complete list — two models**. No Gemma 3, no Gemma 3n, no `gemma-3-27b-it`, no EmbeddingGemma, no E2B/E4B/12B on the hosted API. The smaller Gemma 4 sizes exist as open weights only.

**Confidence: HIGH.** Directly quoted from the page.

### Cross-check: the Gemini API model list page does NOT list Gemma

Fetched https://ai.google.dev/gemini-api/docs/models and grepped the full rendered text case-insensitively for `gemma`:

```
--- models.txt: gemini=<many> gemma=0
```

**Zero occurrences.** The models page lists only Gemini / Imagen / Veo / Lyria / embedding / robotics models (e.g. `gemini-3.8-flash`, `gemini-3.1-pro-preview`, `gemini-3.5-flash-lite`, `gemini-embedding-001`, `veo-3.1-generate-preview`). Gemma is documented exclusively on the `/gemma/` microsite.

**Implication for the build:** do not expect the Gemma IDs to show up in capability tables, "supported tools per model" matrices, or the rate-limit tables. They won't.

---

## 2. Is there a Gemma 4 generation as of 2026-10-03? YES

Source: https://ai.google.dev/gemma/docs/releases

Verbatim release log entries (most recent first):

```
June 3, 2026
Release of Gemma 4 12B Unified.

April 16, 2026
Release of Gemma 4 - MTP for E2B, E4B, 31B, and 26B A4B.

March 31, 2026
Release of Gemma 4 in E2B, E4B, 31B and 26B A4B sizes.

January 15, 2026
Release of TranslateGemma in 4B, 12B, and 27B parameter size.
```

Site-wide banner on every Gemma doc page:

```
Gemma 4 released with text, audio and image input and long up to 256K context window! Learn more
```

**Latest Gemma generation = Gemma 4.** Gemma 3 and Gemma 3n are the previous generations (Gemma 3n E2B/E4B released 2025; Gemma 3 1B/4B/12B/27B released 2025). There is no Gemma 5.

**Confidence: HIGH.**

### Served ID naming convention

Hosted Gemini API IDs are lowercase with an `-it` suffix (instruction-tuned):

- `gemma-4-26b-a4b-it`
- `gemma-4-31b-it`

Hugging Face / open-weights IDs use a **different casing** (capital B, capital A4B). Verbatim from https://ai.google.dev/gemma/docs/capabilities/vision/image and https://ai.google.dev/gemma/docs/capabilities/thinking:

```python
MODEL_ID = "google/gemma-4-E2B-it" # @param ["google/gemma-4-E2B-it", "google/gemma-4-E4B-it", "google/gemma-4-12B-it", "google/gemma-4-31B-it", "google/gemma-4-26B-A4B-it"]
```

So the five open sizes are `E2B`, `E4B`, `12B`, `26B-A4B`, `31B` — but **only `26b-a4b` and `31b` are hosted**. Do not send `gemma-4-12b-it` or `gemma-4-e4b-it` to the Gemini API; they are not listed as supported.

**Confidence: HIGH** for the hosted two; **HIGH** that the other three are open-weights-only (absent from the supported list).

---

## 3. Gemma 4 26B A4B — model card facts

Source: https://ai.google.dev/gemma/docs/core/model_card_4

Verbatim intro:

> "Gemma is a family of open models built by Google DeepMind. Gemma 4 models are multimodal, handling text and image input (with audio supported on E2B, E4B, and 12B models) and generating text output. This release includes open-weights models in both pre-trained and instruction-tuned variants. Gemma 4 features a context window of up to 256K tokens and maintains multilingual support in over 140 languages. Featuring both Dense and Mixture-of-Experts (MoE) architectures, Gemma 4 is well-suited for tasks like text generation, coding, and reasoning. The models are available in five distinct sizes: E2B, E4B, 12B, 26B A4B, and 31B."

MoE table, verbatim values for the model LetterLens would use:

| Property | 26B A4B MoE |
|---|---|
| Total Parameters | 25.2B |
| Active Parameters | 3.8B |
| Layers | 30 |
| Sliding Window | 1024 tokens |
| Context Length | 256K tokens |
| Vocabulary Size | 262K |
| Expert Count | 8 active / 128 total and 1 shared |
| Supported Modalities | **Text, Image** |
| Vision Encoder Parameters | ~550M |

And `gemma-4-31b-it` (the dense alternative):

| Property | 31B Dense |
|---|---|
| Total Parameters | 30.7B |
| Layers | 60 |
| Context Length | 256K tokens |
| Supported Modalities | **Text, Image** |
| Vision Encoder Parameters | ~550M |
| Audio | No Audio |

**Note: neither hosted model supports audio input.** Audio is "featured natively on the E2B, E4B, and 12B models" — none of which are on the Gemini API.

Declared capability advancements, verbatim:

> "Reasoning – All models in the family are designed as highly capable reasoners, with configurable thinking modes."
> "Extended Multimodalities – Processes Text, Image with variable aspect ratio and resolution support (all models), Video, and Audio (featured natively on the E2B, E4B, and 12B models)."
> "Enhanced Coding & Agentic Capabilities – Achieves notable improvements in coding benchmarks alongside native function-calling support, powering highly capable autonomous agents."
> "Native System Prompt Support – Gemma 4 introduces native support for the `system` role, enabling more structured and controllable conversations."

Selected benchmarks (instruction-tuned):

| | Gemma 4 31B | Gemma 4 26B A4B | Gemma 3 27B (no think) |
|---|---|---|---|
| MMLU Pro | 85.2% | 82.6% | 67.6% |
| AIME 2026 no tools | 89.2% | 88.3% | 20.8% |
| LiveCodeBench v6 | 80.0% | 77.1% | 29.1% |

**Confidence: HIGH.**

---

## 4. Capability support, item by item

### 4.1 Multimodal / image input — SUPPORTED ✅

Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api

Verbatim:

> "**Image Understanding**
> Gemma 4 models can process images, enabling many frontier developer use cases that would have historically required domain specific models."

Python example, verbatim:

```python
from google import genai

client = genai.Client()

my_file = client.files.upload(file="path/to/sample.jpg")

response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents=[my_file, "Caption this image."],
)

print(response.text)
```

REST example, verbatim (the official doc uses the **Files API** — `file_data` / `file_uri`, NOT inline base64):

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{
        "parts":[
          {"file_data":{"mime_type": "'"${MIME_TYPE}"'", "file_uri": "'"${file_uri}"'"}},
          {"text": "Caption this image."}]
        }]
      }' 2> /dev/null > response.json
```

**⚠️ `inlineData` + base64 for Gemma is NOT shown in any primary Google doc.** The Gemma page only demonstrates the Files API upload path. The Gemma vision capability page (https://ai.google.dev/gemma/docs/capabilities/vision/image) is a Hugging Face `transformers` notebook, not a Gemini API guide — it contains zero occurrences of `inline_data`, `inlineData` or `base64`.

**Confidence that image input works on `gemma-4-26b-a4b-it` via the Gemini API: HIGH.**
**Confidence that `inlineData` base64 works for Gemma specifically: MEDIUM.** Reasoning: (a) `inlineData` is a generic field on the API-wide `Part` type, not a per-model feature — see the API reference below; (b) a third-party walkthrough by Philipp Schmid (Google DeepMind) uses the inline-bytes path with a Gemma model. Still, no Google doc page demonstrates it with a Gemma ID. **Test this on day one.**

The generic inline shape (from the **legacy** Gemini image doc, `gemini-3.8-flash` substituted in the sample) — https://ai.google.dev/gemini-api/docs/generate-content/image-understanding:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
-H "x-goog-api-key: $GEMINI_API_KEY" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
    "contents": [{
    "parts":[
        {
            "inline_data": {
            "mime_type":"image/jpeg",
            "data": "'"$(base64 $B64FLAGS $IMG_PATH)"'"
            }
        },
        {"text": "Caption this image."},
    ]
    }]
}'
```

API-reference definition of the `Blob` type (https://ai.google.dev/api/generate-content):

> **Blob** — "Raw media bytes. Text should not be sent as raw bytes, use the 'text' field."
> `mimeType` — string — "The IANA standard MIME type of the source data. Examples of supported types: - Images: image/png, image/jpeg, image/jpg, image/webp, image/heic, image/heif, image/gif, image/avif …"
> `data` — string (bytes format)

And on `Part`:

> "A Part must have a fixed IANA MIME type identifying the type and subtype of the media if the `inlineData` field is filled with raw bytes."
> `inlineData` — object (Blob) — "Inline media bytes."

Supported image MIME types, verbatim from the legacy image-understanding doc:

```
Supported image formats
Gemini supports the following image format MIME types:
PNG - image/png
JPEG - image/jpeg
WEBP - image/webp
HEIC - image/heic
HEIF - image/heif
```

Inline size limit, verbatim:

> "Note: Inline image data limits your total request size (text prompts, system instructions, and inline bytes) to 20MB. For larger requests, upload image files using the File API."

**OCR on Gemma is explicitly demonstrated** (relevant: LetterLens reads letters). From https://ai.google.dev/gemma/docs/capabilities/vision/image:

> "**OCR (Optical Character Recognition)** — Models can recognize multilingual texts in the image."

…with a worked example where the model correctly reads Japanese signage. Also documented on the same page:

> "**Object Detection** — Models are trained to detect objects in an image and get their bounding box coordinates. Bounding box coordinates are expressed as normalized values relative to a 1000x1000 grid. You need to descale these coordinates based on your original image size."

(Those two are demonstrated on local HF weights, so they describe *model* capability, not a guarantee of the hosted endpoint — but the hosted model is the same weights.)

### 4.2 Function calling / tools — SUPPORTED ✅ (explicitly, for Gemma, on the Gemini API)

Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api

Verbatim:

> "**Function Calling**
> Define tools as function declarations. The model decides when to call them:"

REST, verbatim — note it uses the Gemma model ID:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "Should I bring an umbrella to Kyoto today?"}]
  }],
  "tools": [{
    "functionDeclarations": [{
      "name": "get_weather",
      "description": "Get current weather for a given location.",
      "parameters": {
        "type": "OBJECT",
        "properties": {
          "location": {
            "type": "STRING",
            "description": "City and state, e.g. 'San Francisco, CA'"
          }
        },
        "required": ["location"]
      }
    }]
  }]
}'
```

Python, verbatim:

```python
from google import genai
from google.genai import types

# Define the function declaration
get_weather = {
    "name": "get_weather",
    "description": "Get current weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and state, e.g. 'San Francisco, CA'",
            },
        },
        "required": ["location"],
    },
}

client = genai.Client()
tools = types.Tool(function_declarations=[get_weather])
config = types.GenerateContentConfig(tools=[tools])

response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents="Should I bring an umbrella to Kyoto today?",
    config=config,
)

# The model returns a function call instead of text
if response.function_calls:
    for fc in response.function_calls:
        print(f"Function to call: {fc.name}")
        print(f"ID: {fc.id}")
        print(f"Arguments: {fc.args}")
else:
    print("No function call found in the response.")
    print(response.text)
```

Note the REST form uses **uppercase OpenAPI types** (`"OBJECT"`, `"STRING"`) while the SDK form uses lowercase (`"object"`, `"string"`). Both appear on the same page; copy whichever matches your transport.

**Confidence: HIGH.** This is the strongest single answer in the whole note — function calling is NOT Gemini-models-only, and it is demonstrated with the exact model ID the spec names.

**→ This is the recommended route to structured data out of Gemma.** Since `responseFormat` is undocumented for Gemma (§4.3), a single-tool forced function call is the documented way to get a typed JSON object out of `gemma-4-26b-a4b-it`.

### 4.3 Structured output / `responseSchema` / `responseMimeType: application/json` — NOT CONFIRMED ⚠️

**I could not confirm this from any primary doc.**

Evidence gathered:

- https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api — the full page text was read end to end. Sections present: Supported Models, Get API Key, Thinking, Image Understanding, System Instructions, Multi-turn Conversations, Function Calling, Google Search. **There is no structured-output section and no mention of `responseFormat`, `responseSchema`, `responseMimeType` or JSON mode anywhere on the page.**
- https://ai.google.dev/gemini-api/docs/structured-output — grepped for `gemma`: **0 occurrences**. Every example uses `gemini-3.8-flash` or `gemini-3.1-pro-preview`.
- https://ai.google.dev/gemini-api/docs/generate-content/structured-output (the legacy variant) — grepped for `gemma`: **0 occurrences**.

The docs do **not** say Gemma is excluded. They simply never mention it. So the honest position is: **unknown, must be tested against a live key.**

For when you test it, here is the current field shape. The non-deprecated field is `responseFormat`, verbatim from https://ai.google.dev/gemini-api/docs/generate-content/structured-output:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{ "parts":[ { "text": "..." } ] }],
      "generationConfig": {
        "responseFormat": {
          "text": {
            "mimeType": "application/json",
            "schema": { "type": "object", "properties": { ... }, "required": [ ... ] }
          }
        }
      }
    }'
```

And from the API reference (https://ai.google.dev/api/generate-content), on `GenerationConfig`:

> `responseFormat` — object (ResponseFormatConfig) — "Optional. Configuration for the response output format. Allows specifying output configuration per modality (text, audio, image) in a flat structure."
>
> `responseMimeType` — string — "Optional. MIME type of the generated candidate text. Supported MIME types are: `text/plain`: (default) Text output. `application/json`: JSON response in the response candidates. `text/x.enum`: ENUM as a string response in the response candidates."
>
> `responseSchema` **(deprecated)** — object (Schema) — "This item is deprecated! … If set, a compatible responseMimeType must also be set. Compatible MIME types: `application/json`… **Deprecated. Use `responseFormat` instead.**"
>
> `_responseJsonSchema` **(deprecated)** — "This item is deprecated! Optional. Output schema of the generated response. This is an alternative to responseSchema that accepts JSON Schema. If set, responseSchema must be omitted, but responseMimeType is required."

**Confidence: LOW that structured output works on Gemma. HIGH on the field names/shape themselves (for Gemini models).**

**Build recommendation:** do not architect around `responseFormat` for Gemma. Use function calling (§4.2), which *is* documented for Gemma, and keep a prompt-plus-`JSON.parse` fallback. Probe `responseFormat` once with a real key; if it 400s with `INVALID_ARGUMENT`, you have your answer in one request.

### 4.4 Streaming (`streamGenerateContent` / `alt=sse`) — NOT CONFIRMED ⚠️

**I could not confirm this for Gemma from any primary doc.**

- The Gemma-on-Gemini-API page has **no streaming section and no occurrence of `streamGenerateContent`**. Every one of its ten REST samples calls `:generateContent` (non-streaming).
- https://ai.google.dev/api/generate-content documents `models.streamGenerateContent` as a generic method on `{model=models/*}` — i.e. it is **defined for any model resource**, not enumerated per model.
- No Gemini doc page that discusses streaming mentions Gemma (grepped `textgen.txt`, `ltextgen.txt`, `apiref.txt` → `gemma: 0`).

The method definition, verbatim from the API reference:

```
Method: models.streamGenerateContent

Endpoint
  post
https://generativelanguage.googleapis.com/v1beta/{model=models/*}:streamGenerateContent
```

**Confidence: LOW–MEDIUM that it works for Gemma.** Because `streamGenerateContent` is a path-templated method over the generic `models/*` resource rather than a per-model capability flag, it most likely works — but that is inference, not documentation. Test it.

### 4.5 System instructions — SUPPORTED ✅

Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api

Verbatim:

> "**System Instructions**
> You can pass a system instruction to set the model's behavior:"

REST, verbatim, with the Gemma model ID:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "What is the purpose of the tea ceremony?"}]
  }],
  "systemInstruction": {
    "parts": [{"text": "You are a wise Kyoto tea master. Speak calmly and poetically, using nature metaphors. Keep answers under 3 sentences."}]
  }
}'
```

Python, verbatim:

```python
response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    config=types.GenerateContentConfig(
        system_instruction="You are a wise Kyoto tea master. Speak calmly and poetically, using nature metaphors. Keep answers under 3 sentences."
    ),
    contents="What is the purpose of the tea ceremony?"
)
```

Corroborated by the model card:

> "**Native System Prompt Support** – Gemma 4 introduces native support for the `system` role, enabling more structured and controllable conversations."

**This is a genuine change from Gemma 3.** Gemma 1/2/3 had no `system` role and required folding the system prompt into the first user turn — that is why the Gemma docs carry a page titled "Legacy Prompt and system instructions [Gemma 1, 2, and 3]". **For Gemma 4 you do NOT need to fold the system prompt into the first user turn.** Use `systemInstruction` directly.

**Confidence: HIGH.**

### 4.6 Thinking / `thinkingConfig` / `thinkingLevel` — SUPPORTED for Gemma 4, and "minimal" is the documented off-switch ✅

Source: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api

Verbatim:

> "**Thinking**
> Gemma 4 utilizes an internal "thinking process" that optimizes its multi-step reasoning, delivering superior performance in logically demanding domains such as algorithmic coding and advanced mathematical proofs.
>
> While Gemma 4 **strictly supports toggling this feature on or off**, you can control it using the API by setting the thinking level to `"high"` for enabled or `"minimal"` for disabled."

REST, verbatim:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "What is the water formula?"}]
    }],
    "generationConfig": {
      "thinkingConfig": {
            "thinkingLevel": "high"
      }
    }
   }'
```

Python, verbatim:

```python
response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents="What is the water formula?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high")
    ),
)
```

JavaScript, verbatim:

```javascript
import { GoogleGenAI, ThinkingLevel } from "@google/genai";

const response = await ai.models.generateContent({
  model: "gemma-4-26b-a4b-it",
  contents: "What is the water formula?",
  config: {
    thinkingConfig: {
      thinkingLevel: ThinkingLevel.HIGH,
    },
  },
});
```

**⚠️ Important nuance — a documented conflict.** The API reference says of `thinkingLevel`:

> "Optional. Controls the maximum depth of the model's internal reasoning process before it produces a response. The default value is model-dependent. Refer to the Thinking levels guide for more details. **Recommended for Gemini 3 or later models. Use with earlier models results in an error.**"
> — https://ai.google.dev/api/generate-content

The full `ThinkingLevel` enum, verbatim:

```
THINKING_LEVEL_UNSPECIFIED  | Default value.
MINIMAL                     | Little to no thinking.
LOW                         | Low thinking level.
MEDIUM                      | Medium thinking level.
HIGH                        | High thinking level.
```

So the enum carries five values, but the Gemma page says **Gemma 4 only honours the two extremes** — `"high"` = on, `"minimal"` = off. Do not send `low` or `medium` to Gemma and expect graded behaviour.

So, answering the spec's question directly: **`thinkingConfig` with level `"minimal"` DOES apply to Gemma 4** — it is not Gemini-2.5+/3-only. The Gemma doc demonstrates it with the exact model ID.

Local-weights corroboration of the on/off-only design, from https://ai.google.dev/gemma/docs/capabilities/thinking:

> "Note: We've added an empty thinking token to the chat template for `gemma-4-12B-it`, `gemma-4-26B-A4B-it` and `gemma-4-31B-it`. This stabilizes model output by suppressing "ghost" thought channels that may appear even when thinking is deactivated."

**Confidence: HIGH** that `thinkingLevel: "high" | "minimal"` is correct for Gemma 4 on the Gemini API.

### 4.7 Google Search grounding — DOCUMENTED but CONTRADICTED by the pricing page ⚠️

The Gemma page documents it, verbatim:

> "**Google Search**
> Ground Gemma 4 responses in real-time web data with Google Search:"

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "What are the dates for cherry blossom season in Tokyo this year?"}]
  }],
  "tools": [{"googleSearch": {}}]
}'
```

But https://ai.google.dev/gemini-api/docs/pricing, in its **Gemma 4** block, says:

```
Grounding with Google Search |  Not available  |  Not available
```

(i.e. "Not available" on both Free Tier and Paid Tier.)

**These two primary Google pages disagree.** Flagging it rather than picking a side. LetterLens almost certainly does not need search grounding for reading a letter, so this should not block the build — but do not design a feature on it.

**Confidence: LOW** on whether Google Search grounding actually works with Gemma. **HIGH** that the two docs conflict.

### 4.8 Multi-turn chat — SUPPORTED ✅

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "What are the three most famous castles in Japan?" }]
    },
    {
      "role": "model",
      "parts": [{ "text": "Himeji Castle, Matsumoto Castle, and Kumamoto Castle are often considered the top three." }]
    },
    {
      "role": "user",
      "parts": [{ "text": "Which one should I visit in spring for cherry blossoms?" }]
    }
  ]
}'
```

Roles are `"user"` and `"model"` (not `"assistant"`). **Confidence: HIGH.**

---

## 5. Exact REST endpoint shapes

### 5.1 Non-streaming — what the Gemma doc actually uses

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent
```

API-reference canonical form (https://ai.google.dev/api/generate-content):

```
https://generativelanguage.googleapis.com/v1beta/{model=models/*}:generateContent
```

Minimal working call, verbatim from the Gemma page:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "Roses are red..."}]
    }]
   }'
```

> ⚠️ Note this sample **omits the API key entirely** — the Gemma page's curl examples are incomplete. You must add auth yourself (see §5.3).

### 5.2 Streaming

```
POST https://generativelanguage.googleapis.com/v1beta/{model=models/*}:streamGenerateContent
```

Verbatim current-doc example with `?alt=sse` and the header auth form (https://ai.google.dev/gemini-api/docs/generate-content/text-generation):

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:streamGenerateContent?alt=sse" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  --no-buffer \
  -d '{
    "contents": [ { "parts": [ { "text": "..." } ] } ]
  }'
```

Older API-reference samples use the query-param key form instead (https://ai.google.dev/api/generate-content):

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:streamGenerateContent?alt=sse&key=${GEMINI_API_KEY}" \
        -H 'Content-Type: application/json' \
        --no-buffer \
        -d '{ "contents":[{"parts":[{"text": "Write a story about a magic backpack."}]}]}'
```

Key points:
- `?alt=sse` is **required** to get Server-Sent Events. Without it, `streamGenerateContent` returns a streamed **JSON array**, not SSE.
- `--no-buffer` on curl is used in every official sample.
- Substituting `gemma-4-26b-a4b-it` into the path is **unverified** — see §4.4.

### 5.3 API key: `x-goog-api-key` header vs `?key=`

**Both work. The header is what current docs use.**

- `-H "x-goog-api-key: $GEMINI_API_KEY"` — used throughout the current docs: the image-understanding, text-generation, structured-output and `interactions` pages all use it exclusively (21+ occurrences across the pages fetched).
- `?key=${GEMINI_API_KEY}` — still present in the `/api/generate-content` reference samples (6 occurrences, all alongside `alt=sse`).

**Recommendation: use the `x-goog-api-key` header.** It keeps the key out of URLs, logs, and referrers — which matters for LetterLens, since a hackathon demo URL with a key in the query string is the classic leak. Both are accepted by the service.

**Confidence: HIGH** on both forms being accepted; **HIGH** that the header is the currently-documented default.

### 5.4 ⚠️ There is a NEWER API surface that does not mention Gemma

As of this research date, the main Gemini API docs have moved to:

```
POST https://generativelanguage.googleapis.com/v1beta/interactions
POST https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse
```

…with a flat `{"model": "...", "input": ...}` body and `response_format` for schemas. Example verbatim from https://ai.google.dev/gemini-api/docs/text-generation:

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  --no-buffer \
  -d '{ "model": "gemini-3.8-flash", "input": "..." }'
```

The old pages now live under `/gemini-api/docs/generate-content/*` and their `<title>` reads **"… | Gemini Generate Content API (Legacy) | Google AI for Developers"**.

**The Gemma page is written entirely against the legacy `:generateContent` surface, and no `interactions` page mentions Gemma at all (0 hits across every `interactions` doc fetched).**

**Build implication:** target `:generateContent` for Gemma, as the Gemma doc does. Do not try to call Gemma through `/v1beta/interactions` — it is undocumented for Gemma and may reject the model. **Confidence: HIGH** that `:generateContent` is the right surface for Gemma; **LOW** on whether `interactions` accepts Gemma IDs at all.

---

## 6. Rate limits and free-tier availability

### 6.1 Pricing page — Gemma 4 is FREE-TIER-ONLY

Source: https://ai.google.dev/gemini-api/docs/pricing

Verbatim Gemma 4 block:

```
Gemma 4
Our lightweight, state-of the art, open model built from the same technology
that powers our Gemini models.

                            | Free Tier         | Paid Tier, per 1M tokens in USD
Input price                 | Free of charge    | Not available
Output price                | Free of charge    | Not available
Context caching price       | Free of charge    | Not available
Context caching (storage)   | Free of charge    | Not available
Tuning price                | Not available     | Not available
Grounding with Google Search| Not available     | Not available
Used to improve our products| Yes               | No
```

Three things that matter a great deal for a hackathon build:

1. **Gemma 4 is free of charge.** Zero cost for input and output. Perfect for a hackathon.
2. **There is NO paid tier for Gemma 4** — every paid-tier cell reads "Not available". So you **cannot buy your way past the free-tier rate limits** for Gemma. If LetterLens hits the free-tier ceiling during a live demo, your only escape is switching models, not adding billing.
3. **"Used to improve our products: Yes"** on the free tier. For an app that reads people's personal letters, this is a real privacy consideration. Free-tier Gemini API data is used for product improvement. Put this in your demo's disclosure, and do not feed real personal correspondence through it without saying so.

**Confidence: HIGH** — directly quoted from the pricing page.

### 6.2 Specific RPM/TPM/RPD numbers for Gemma — NOT DOCUMENTED

Source: https://ai.google.dev/gemini-api/docs/rate-limits (page footer: *Last updated 2026-09-02 UTC*)

Grepped the full rendered page for `gemma`: **0 occurrences.** Gemma appears in none of the rate-limit tables.

Worse, the page no longer publishes per-model numbers for anything. Verbatim:

> "**Gemini API rate limits**
> Rate limits depend on a variety of factors (such as your usage tier) and can be viewed in Google AI Studio. As your tier and account status change over time, your rate limits will automatically update.
> View your active rate limits in AI Studio
> Specified rate limits are not guaranteed and actual capacity may vary."

and:

> "Each model variation has an associated rate limit (requests per minute, RPM). For details on those rate limits, see the AI Studio Rate Limit page."

What *is* documented (verbatim), for context:

> "Rate limits are applied per project, not per API key."

Usage tiers table, verbatim:

```
Usage tier | Qualification                                      | Billing tier cap
Free       | Active project or free trial                       | N/A
Tier 1     | Set up and link an active billing account           | $250
Tier 2     | Paid $100 + 3 days from first successful payment    | $2,000
Tier 3     | Paid $1,000 + 30 days from first successful payment | $20,000 - $100,000+
```

Spend-based limits, verbatim:

```
Usage tier | Spend rate limit (per 10 minutes)
Free       | N/A
Tier 1     | $10
Tier 2     | $50
Tier 3     | $200
```

> "If you hit a spend-based rate limit, the API returns a 429 RESOURCE_EXHAUSTED error."

**Confidence: HIGH that Gemma rate limits are not published. LOW/unknown on the actual numbers** — you must read them from the AI Studio rate-limit page with your own key.

**Build implication:** budget for `429 RESOURCE_EXHAUSTED`. Implement exponential backoff and a visible "we're rate-limited, retrying" state before demo day. Since Gemma has no paid tier, a 429 cannot be bought away.

---

## 7. OpenAI-compatibility endpoint and Gemma

Source: https://ai.google.dev/gemini-api/docs/openai

Grepped the full rendered page for `gemma`: **0 occurrences.** The page opens, verbatim:

> "**Gemini models** are accessible using the OpenAI libraries (Python and TypeScript / Javascript) along with the REST API, by updating three lines of code and using your Gemini API key. If you aren't already using the OpenAI libraries, we recommend that you call the Gemini API directly."

Note the wording: "**Gemini models**". Gemma is never named.

**Does it accept Gemma model IDs? I could not confirm this. Treat as LOW confidence / unverified.** A targeted web search for Gemma IDs on the Gemini OpenAI-compat endpoint turned up nothing authoritative either — only third-party gateways (Vercel AI Gateway, OpenRouter, DeepInfra, Cloudflare Workers AI) that serve `gemma-4-26b-a4b-it` through *their own* OpenAI-compatible endpoints, which is a different thing entirely.

### What the endpoint definitely supports (for Gemini models)

Base URL, verbatim:

```python
from openai import OpenAI

client = OpenAI(
    api_key="GEMINI_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

**`"stream": true` — YES, documented.** Verbatim:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer GEMINI_API_KEY" \
  -d '{
      "model": "gemini-3.8-flash",
      "messages": [
          {"role": "user", "content": "Explain to me how AI works"}
      ],
      "stream": true
    }'
```

**`"tools"` — YES, documented.** Verbatim:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer GEMINI_API_KEY" \
-d '{
  "model": "gemini-3.8-flash",
  "messages": [
    { "role": "user", "content": "What'\''s the weather like in Chicago today?" }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": { "type": "string", "description": "The city and state, e.g. Chicago, IL" },
            "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}'
```

Note the auth header here is `Authorization: Bearer $GEMINI_API_KEY`, **not** `x-goog-api-key`. Other documented routes on this base URL: `/chat/completions`, `/embeddings`, `/images/generations`, `/videos`. Thinking is exposed as OpenAI-style `reasoning_effort` (e.g. `"reasoning_effort": "low"`).

**Verdict: `stream` and `tools` work on the OpenAI-compat endpoint — for Gemini models. Whether `gemma-4-26b-a4b-it` is accepted there is UNVERIFIED (LOW confidence). One curl with your key settles it.**

---

## 8. Verdict for the LetterLens build

### The spec's model ID is correct. Use it.

`gemma-4-26b-a4b-it` is real, hosted, free, multimodal (text + image), 256K context, and the Gemini API documents it with the exact capabilities the spec presumably wants. **No fallback is needed on grounds of the model not existing.**

### Can a Gemma model do the vision task at all? YES.

`gemma-4-26b-a4b-it` takes image input on the Gemini API ("Gemma 4 models can process images"), carries a ~550M-parameter vision encoder, supports variable aspect ratio and resolution, and the Gemma docs explicitly demonstrate **multilingual OCR** and bounding-box object detection. For reading a scanned or photographed letter, this is squarely in scope.

### Recommended build posture

| Concern | Decision |
|---|---|
| Primary model | `gemma-4-26b-a4b-it` — free, MoE (~3.8B active params ⇒ fast), 256K context, vision |
| Surface | Legacy `POST /v1beta/models/{id}:generateContent` — **not** `/v1beta/interactions` |
| Auth | `x-goog-api-key` header |
| Image transport | Start with **Files API** (`file_data`/`file_uri`), the only documented path for Gemma. Probe `inline_data` base64 immediately; if it works, prefer it (simpler, one round trip, 20MB cap) |
| Structured data out | **Function calling** (documented for Gemma). Do NOT depend on `responseFormat`/`responseSchema` |
| Thinking | `"thinkingConfig": {"thinkingLevel": "minimal"}` for fast UI paths, `"high"` for careful extraction. Only these two values |
| System prompt | Use `systemInstruction` directly — Gemma 4 has native `system` role support. No folding needed |
| Streaming | Assume it works, but **verify before relying on it for UX** |
| Rate limits | Unknown and unpublished. Build 429 backoff. There is **no paid tier** to escape to |
| Privacy | Free tier ⇒ "Used to improve our products: Yes". Disclose this if real letters are used |

### Fallback model, if a Gemma capability turns out to be missing

If structured output or streaming turns out to be unsupported on Gemma and the build genuinely needs them, the nearest documented alternative on the same API is **`gemini-3.8-flash`** — it is the model used in essentially every current Gemini API example (text generation, structured output, function calling, image understanding, OpenAI-compat), so every shape in this note is verified against it. It is multimodal, supports `responseFormat`, `streamGenerateContent?alt=sse`, `tools`, and the OpenAI-compat endpoint. The trade is that it is a paid/metered Gemini model rather than a free Gemma one.

Cheaper documented Gemini options if cost matters: `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`.

---

## 9. Open questions to settle with one API key (≈5 minutes of curl)

1. Does `inline_data` + base64 work with `gemma-4-26b-a4b-it`? *(most important for LetterLens)*
2. Does `generationConfig.responseFormat` work with Gemma, or 400?
3. Does `:streamGenerateContent?alt=sse` work with Gemma?
4. Does `/v1beta/openai/chat/completions` accept `"model": "gemma-4-26b-a4b-it"`?
5. What are the actual free-tier RPM/RPD for Gemma in AI Studio?
6. Does `"tools": [{"googleSearch": {}}]` work, or does the pricing page's "Not available" win?

Quick probe for (1) + (2) combined:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [{
      "parts": [
        {"inline_data": {"mime_type": "image/jpeg", "data": "'"$(base64 -w0 letter.jpg)"'"}},
        {"text": "Extract the sender, date and subject from this letter."}
      ]
    }],
    "generationConfig": {
      "responseFormat": {
        "text": {
          "mimeType": "application/json",
          "schema": {
            "type": "object",
            "properties": {
              "sender": {"type": "string"},
              "date": {"type": "string"},
              "subject": {"type": "string"}
            },
            "required": ["sender", "date", "subject"]
          }
        }
      }
    }
  }'
```

If that 400s, drop `generationConfig` and retry to isolate which half failed.

---

## 10. Source index

| # | URL | What it established | Last updated (per page) |
|---|---|---|---|
| 1 | https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api | The two hosted Gemma IDs; image, function calling, system instructions, thinking, Google Search, multi-turn; all REST shapes | 2026-07-02 UTC |
| 2 | https://ai.google.dev/gemini-api/docs/models | Gemma is absent (0 hits) | — |
| 3 | https://ai.google.dev/gemma/docs/releases | Gemma 4 released 2026-03-31; latest generation | — |
| 4 | https://ai.google.dev/gemma/docs/core/model_card_4 | 26B A4B specs: 25.2B total / 3.8B active, 256K ctx, Text+Image, no audio; native system role | — |
| 5 | https://ai.google.dev/gemma/docs/capabilities/vision/image | OCR + object detection capability; open-weights model ID casing | — |
| 6 | https://ai.google.dev/gemma/docs/capabilities/thinking | Thinking on/off design; chat-template note for 26B A4B | — |
| 7 | https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4 | Function calling (HF ecosystem variant) | — |
| 8 | https://ai.google.dev/gemini-api/docs/pricing | Gemma 4 free-tier-only; no paid tier; search grounding "Not available"; data used for product improvement | — |
| 9 | https://ai.google.dev/gemini-api/docs/rate-limits | Gemma absent (0 hits); per-model limits no longer published; tier tables; 429 RESOURCE_EXHAUSTED | 2026-09-02 UTC |
| 10 | https://ai.google.dev/gemini-api/docs/openai | OpenAI-compat base URL, `stream`, `tools`, `reasoning_effort`; Gemma absent (0 hits) | — |
| 11 | https://ai.google.dev/gemini-api/docs/structured-output | New `interactions` + `response_format`; Gemma absent (0 hits) | — |
| 12 | https://ai.google.dev/gemini-api/docs/generate-content/structured-output | Legacy `:generateContent` + `generationConfig.responseFormat`; page titled "(Legacy)"; Gemma absent | — |
| 13 | https://ai.google.dev/gemini-api/docs/generate-content/text-generation | `streamGenerateContent?alt=sse` + `x-goog-api-key` | — |
| 14 | https://ai.google.dev/gemini-api/docs/generate-content/image-understanding | `inline_data` shape, supported MIME types, 20MB inline cap | — |
| 15 | https://ai.google.dev/api/generate-content | Method definitions, `Blob`, `Part`, `ThinkingLevel` enum, `responseFormat` vs deprecated `responseSchema` | — |
| 16 | https://ai.google.dev/gemini-api/docs/text-generation | New `/v1beta/interactions?alt=sse` surface | — |
| 17 | https://www.philschmid.de/gemma-4-gemini-api (third-party, 2026-04-07) | Corroborates the two hosted IDs; uses `types.Part.from_bytes(...)` inline-bytes path with a Gemma model | — |

Third-party listings also confirming `gemma-4-26b-a4b-it` exists as a real model (non-authoritative for Gemini API behaviour): Vercel AI Gateway, OpenRouter, DeepInfra, Cloudflare Workers AI, Inworld.
