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

---

## Independent verification (adversarial pass)

**Verifier:** second agent, independent re-fetch. **Date:** 2026-10-03.
**Method:** I did not trust any URL cited above. I re-fetched all 14 pages myself with `curl -sL` (all HTTP 200), stripped `<script>/<style>/<svg>` and tags to plain text, and ran exact-string counts and verbatim extractions against the text. Where a count is quoted below it is a real `grep`/`str.count` over a page I fetched in this task, not a recollection. I also fetched one page the note never cites (`prompt-formatting-gemma4`), which turned out to matter.

**Headline: the research note holds up.** `gemma-4-26b-a4b-it` is real, the two-model list is exact, and every "NOT CONFIRMED" label is correctly applied. I found **no hallucinated model ID, no hallucinated npm package, and no hallucinated field name.** The npm package `@google/genai` is the only `@google/*` package on the Gemma page (verified by regex-extracting every `@google/*` string: result was exactly `['@google/genai']`) and the Python imports are `from google import genai` / `from google.genai import types`. Five items need correction or softening, all listed below.

### Per-claim verdicts

| # | Claim | Verdict |
|---|---|---|
| 1 | Exactly two Gemma models, `gemma-4-31b-it` + `gemma-4-26b-a4b-it` | **CONFIRMED** |
| 2 | Gemma 4 latest; release log; no Gemma 5 | **CONFIRMED** |
| 3 | Gemini API models page: zero `gemma` | **CONFIRMED** |
| 4 | 26B A4B MoE specs; no audio on hosted models | **CONFIRMED** |
| 5 | Image input supported; only Files API transport documented | **CONFIRMED** |
| 6 | `inline_data` with Gemma unverified but plausible | **CONFIRMED** (as an accurate statement of non-verification) |
| 7 | Function calling documented for Gemma, with REST example | **CONFIRMED** |
| 8 | Structured output for Gemma not confirmed | **CONFIRMED** (+ new corroborating evidence) |
| 9 | `responseFormat.text.{mimeType,schema}`; `responseSchema`/`_responseJsonSchema` deprecated | **CONFIRMED w/ correction** |
| 10 | System instructions supported; no folding needed | **CONFIRMED** (+ independent corroboration) |
| 11 | `thinkingConfig` applies to Gemma 4; only `high`/`minimal` usable | **CONFIRMED** (+ mechanism found) |
| 12 | Full `ThinkingLevel` enum + "Gemini 3 or later" warning | **CONFIRMED w/ caveat** |
| 13 | Streaming for Gemma not confirmed | **CONFIRMED w/ correction** (sample count wrong) |
| 14 | Endpoint shapes incl. `?alt=sse`, `--no-buffer` | **PARTIALLY CONFIRMED** — one sub-claim is undocumented |
| 15 | Both API-key forms; Gemma page omits auth | **CONFIRMED w/ correction** (counts wrong) |
| 16 | New `/v1beta/interactions` surface; old pages "(Legacy)" | **CONFIRMED** |
| 17 | Gemma 4 free-tier-only; "Used to improve our products: Yes" | **CONFIRMED** |
| 18 | Gemma rate limits not published; per-project; 429 | **CONFIRMED** |
| 19 | OpenAI-compat base URL, Bearer auth, stream + tools, Gemini-only wording | **CONFIRMED** |
| 20 | OpenAI-compat + Gemma IDs unverified | **CONFIRMED** (as unverifiable) |
| 21 | Gemma vision docs demonstrate multilingual OCR + 1000x1000 bboxes | **CONFIRMED w/ caveat** |
| 22 | 20MB inline cap; PNG/JPEG/WEBP/HEIC/HEIF | **CONFIRMED w/ important caveat** |
| 23 | Hosted IDs lowercase `-it`; HF IDs different casing; other 3 sizes not hosted | **CONFIRMED** |

### Evidence detail, by claim

**1. CONFIRMED.** https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api — exact text, re-extracted by me:

```
Supported Models
The Gemini API supports the following Gemma 4 models:
gemma-4-31b-it
gemma-4-26b-a4b-it
```

Occurrence counts on that page: `gemma-4-26b-a4b-it` = **22**, `gemma-4-31b-it` = **1**. Note the asymmetry — **`gemma-4-31b-it` appears exactly once, in the list, and in zero code samples.** Every example on the page uses the 26B A4B MoE. Page footer: *Last updated 2026-07-02 UTC*.

**2. CONFIRMED.** https://ai.google.dev/gemma/docs/releases — verbatim, re-extracted:

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

`grep -i "gemma 5"` → **0 hits**. Site banner verbatim: `Gemma 4 released with text, audio and image input and long up to 256K context window!`

**3. CONFIRMED.** https://ai.google.dev/gemini-api/docs/models — case-insensitive `gemma` = **0**. I additionally regex-extracted every model ID on the page; the list is entirely Gemini/Imagen/Veo, e.g. `gemini-3.8-flash`, `gemini-3.8-flash-lite-tts`, `gemini-3.8-live`, `gemini-3.8-live-extended-thinking`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-transcribe`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite`, `gemini-omni-1.1-flash`, `gemini-embedding-001`, `gemini-embedding-2-preview`, `gemini-robotics-er-2-preview`, `imagen-4.0-generate`. No Gemma.

**4. CONFIRMED, all nine values exact.** https://ai.google.dev/gemma/docs/core/model_card_4 — MoE table, verbatim:

```
Mixture-of-Experts (MoE) Model
Property                     26B A4B MoE
Total Parameters             25.2B
Active Parameters            3.8B
Layers                       30
Sliding Window               1024 tokens
Context Length               256K tokens
Vocabulary Size              262K
Expert Count                 8 active / 128 total and 1 shared
Supported Modalities         Text, Image
Vision Encoder Parameters    ~550M
```

Dense table, verbatim, which settles the audio question:

```
Property                     E2B                  E4B                  12B Unified          31B Dense
Total Parameters             2.3B effective       4.5B effective       11.95B               30.7B
Layers                       35                   42                   48                   60
Context Length               128K tokens          128K tokens          256K tokens          256K tokens
Supported Modalities         Text, Image, Audio   Text, Image, Audio   Text, Image, Audio   Text, Image
Vision Encoder Parameters    ~150M                ~150M                -                    ~550M
Audio Encoder Parameters     ~300M                ~300M                -                    No Audio
```

So: audio is on E2B, E4B and 12B Unified; **both hosted models (26B A4B and 31B) are `Text, Image` only.** The audio claim is correct.

New detail the note omits: **E2B/E4B are 128K context, not 256K** — the "256K" headline applies to 12B Unified, 26B A4B and 31B only.

**5. CONFIRMED.** Verbatim: `Gemma 4 models can process images, enabling many frontier developer use cases that would have historically required domain specific models.` Occurrence counts on the Gemma page, all mine: `file_data` = **1**, `file_uri` = **5**, `inline_data` = **0**, `inlineData` = **0**, `base64` = **0**. The only REST image transport shown is the Files API.

Worth flagging for the build: the Gemma page's REST image sample is not one request, it is a **three-`curl` resumable upload** (`X-Goog-Upload-Protocol: resumable`, `X-Goog-Upload-Command: start`, then the bytes, then `:generateContent` with `file_data`), preceded by `MIME_TYPE=$(file -b --mime-type ...)` and `NUM_BYTES=$(wc -c < ...)` and writing a temp header file. The note says "materially more work"; concretely it is three round trips before you can ask a question about the image.

**6. CONFIRMED as an honest non-verification, and the reasoning checks out.** https://ai.google.dev/api/generate-content — I found the `Part` sentence the note quotes, verbatim, at two places in the page text:

> `A Part consists of data which has an associated datatype. A Part can only contain one of the accepted types in Part.data . A Part must have a fixed IANA MIME type identifying the type and subtype of the media if the inlineData field is filled with raw bytes.`

`inlineData` is listed inside `Part.data` as one of a set of **mutually exclusive** fields (`text`, `inlineData`, `functionCall`, …) — i.e. a transport field on the request type, with no per-model gating anywhere in the reference. `Blob` verbatim:

> `Blob` — `Raw media bytes. Text should not be sent as raw bytes, use the 'text' field.`
> `mimeType` string — `The IANA standard MIME type of the source data. Examples of supported types: - Images: image/png, image/jpeg, image/jpg, image/webp, image/heic, image/heif, image/gif, image/avif - Audio: audio/*, video/audio/s16le, video/audio/wav - Video: video/* - Text: text/plain, ... - Applications: ... application/json, ... application/pdf`
> `data` string (bytes format) — `Raw bytes for media formats. A base64-encoded string.`

**Addition the note missed:** `Blob` has a third field, `displayName` — `Optional. Specifies the name used to refer to this blob to the m[odel]`.

I also re-fetched the third-party corroboration at https://www.philschmid.de/gemma-4-gemini-api and confirm it does what the note says — inline bytes against a Gemma ID:

```python
with open("path/to/image.png", "rb") as f:
    image_bytes = f.read()

response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
```

That page also shows no streaming and no structured output for Gemma. **Still unverified against a Google page. Probe it.**

**7. CONFIRMED, and this is the sturdiest claim in the note.** The REST sample on the Gemma page uses the Gemma model ID and uppercase OpenAPI types; I verified the casing counts on that page directly: `"OBJECT"` = 1, `"STRING"` = 1, `"object"` = 2, `"string"` = 2 (the lowercase pair appearing in the Python and JavaScript samples). Verbatim REST fragment:

```
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent"
-d '{
  "contents": [{ "parts":[{"text": "Should I bring an umbrella to Kyoto today?"}] }],
  "tools": [{
    "functionDeclarations": [{
      "name": "get_weather",
      "description": "Get current weather for a given location.",
      "parameters": {
        "type": "OBJECT",
        "properties": { "location": { "type": "STRING", "description": "City and state, e.g. 'San Francisco, CA'" } },
        "required": ["location"]
      }
    }]
  }]
}'
```

JS form verbatim: `config: { tools: [{ functionDeclarations: [get_weather] }] }`, response read via `response.functionCalls` (camelCase in JS, `response.function_calls` in Python). `functionDeclarations` = 2 occurrences on the page.

**8. CONFIRMED — and I found a new, independent piece of evidence pointing the same way.** My counts: Gemma page `responseFormat` = **0**, `responseSchema` = **0**, `responseMimeType` = **0**. https://ai.google.dev/gemini-api/docs/structured-output `gemma` = **0**; https://ai.google.dev/gemini-api/docs/generate-content/structured-output `gemma` = **0**. All three confirmed. I also ran my own targeted search for Gemma + structured output on `ai.google.dev` and found nothing.

**NEW EVIDENCE — a page the researcher never cited:** https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4 documents Gemma 4's actual control tokens. It has `json` = 0 and `schema` = 0 occurrences. Gemma 4 has **dedicated trained-in tokens for tool use** — verbatim:

```
Function Calling
Gemma 4 is trained on six special tokens to manage the "tool use" lifecycle.
Token Pair                Purpose
<|tool> <tool|>           Defines a tool
<|tool_call> <tool_call|> Indicates a model's request to use a tool.
<|tool_response> <tool_response|>  Provides a tool's execution result back to the model.
Note: <|tool_response> acts as an additional stop sequence for the inference engine.

Delimiter for String Values: <|"|>
A single token, <|"|>, is used as a delimiter for all string values within the
structured data blocks. ... All string literals in your function declarations,
calls, and responses must be enclosed using this token (e.g., key:<|"|>string value<|"|>).
```

…and **no token or mechanism for a JSON-schema-constrained response.** That is a second, mechanistic reason to prefer function calling over `responseFormat` as the typed-output path: tool use is in the model's training template, schema-constrained decoding is not. It does not prove `responseFormat` would be rejected — constrained decoding is a serving-layer feature, not a model feature — but it removes the last reason to assume it works.

**9. CONFIRMED, with one correction and one trap.** From https://ai.google.dev/api/generate-content, verbatim:

> `responseMimeType` string — `Optional. MIME type of the generated candidate text. Supported MIME types are: text/plain: (default) Text output. application/json: JSON response in the response candidates. text/x.enum: ENUM as a string response in the response candidates.`
> `responseSchema (deprecated)` object (Schema) — `This item is deprecated! Optional. Output schema of the generated candidate text. Schemas must be a subset of the OpenAPI schema and can be objects, primitives or arrays. If set, a compatible responseMimeType must also be set. … Deprecated. Use responseFormat instead.`
> `_responseJsonSchema (deprecated)` value (Value format) — `This item is deprecated! Optional. Output schema of the generated response. This is an alternative to responseSchema that accepts JSON Schema. If set, responseSchema must be omitted, but responseMimeType is required.`

Counts on that page: `responseFormat` = 4, `responseSchema` = 7, `_responseJsonSchema` = 2, `responseMimeType` = 7. The nested shape is confirmed, verbatim:

> `ResponseFormatConfig` — `…for the response output format. This is a flat object where each optional sub-field configures a specific output modality.` Fields: `text` object (TextResponseFormat), `audio` object (AudioResponseFormat), `image` object (ImageResponseFormat).
> `TextResponseFormat` — `Configuration for text output format.` Fields: `mimeType` **enum (MimeType)** — `Optional. The MIME type of the text output.`; `schema` value (Value format) — `Optional. The JSON schema that the output should conform to. Only applicable when mimeType is APPLICATION_JSON.`

**⚠️ TRAP the note does not mention:** `TextResponseFormat.mimeType` is a **proto enum**, not a free MIME string. Its documented values are:

```
MimeType
Supported MIME types for text output.
Enums
MIME_TYPE_UNSPECIFIED   Default value. This value is unused.
APPLICATION_JSON        JSON output format.
TEXT_PLAIN              Plain text output format.
```

The REST/JSON samples nevertheless write the lowercase MIME string — verbatim from the legacy guide, `"mimeType": "application/json"` — because protobuf JSON accepts the alias. So both spellings should be accepted over REST. But **`text/x.enum` is not a `TextResponseFormat.mimeType` value**; enum-constrained output exists only on the deprecated `responseMimeType` field. If LetterLens ever wants `text/x.enum` it must use the deprecated field.

**CORRECTION to sourcing:** the note attributes the `responseMimeType`/`responseSchema` text loosely. Those names are only on `/api/generate-content`. The **legacy structured-output guide has `responseSchema` = 0 and `responseMimeType` = 0 occurrences** and uses `responseFormat` (9 occurrences) exclusively. The note's curl snippet is correct; the attribution is not. Full verbatim REST sample from that guide, with the auth header:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [{ "parts":[ { "text": "Please extract the recipe from the following text..." } ] }],
    "generationConfig": {
      "responseFormat": {
        "text": {
          "mimeType": "application/json",
          "schema": { "type": "object", "properties": { "recipe_name": { "type": "string", ... } } }
        }
      }
    }
  }'
```

**10. CONFIRMED, plus independent corroboration.** The Gemma page REST sample, verbatim, with the Gemma ID:

```
"systemInstruction": {
  "parts": [{"text": "You are a wise Kyoto tea master. Speak calmly and poetically, using nature metaphors. Keep answers under 3 sentences."}]
}
```

(`systemInstruction` = 2 occurrences on the page.) Model card, verbatim: `Native System Prompt Support — Gemma 4 introduces native support for the system role, enabling more structured and controllable conversations.`

**Independent corroboration at the tokenizer level**, from the page the researcher missed (https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4):

```
Token to indicate a system instruction: system
Token to indicate a user turn: user
Token to indicate a model turn: model
Token to indicate the beginning of a dialogue turn: <|turn>
Token to indicate the end of a dialogue turn: <turn|>

<|turn>system
You are a helpful assistant.<turn|>
<|turn>user
Hello.<turn|>
```

The `system` role exists in the tokenizer itself. **No folding is needed — confirmed from two independent directions.** Note the Gemma 4 turn tokens (`<|turn>`/`<turn|>`) are different from Gemma 1/2/3's `<start_of_turn>`/`<end_of_turn>`; the page opens `Starting with Gemma 4, we introduce new control tokens. For Gemma 3 and lower, see the previous document.`

**11. CONFIRMED verbatim, and I found the mechanism.** Exact sentence from the Gemma page, character-for-character as the claim states it:

> `While Gemma 4 strictly supports toggling this feature on or off, you can control it using the API by setting the thinking level to "high" for enabled or "minimal" for disabled.`

The REST sample is `"generationConfig": { "thinkingConfig": { "thinkingLevel": "high" } }` against `gemma-4-26b-a4b-it`; the JS sample imports `ThinkingLevel` from `@google/genai` and passes `ThinkingLevel.HIGH`; Python passes `types.ThinkingConfig(thinking_level="high")`. `thinkingLevel` = 2 occurrences on the page.

**WHY it is binary** — from prompt-formatting-gemma4, which the note never cites:

```
Thinking Mode
To activate thinking mode, include the <|think|> control token within the
system instruction.
Control Token           Purpose
<|think|>               Activates thinking mode
<|channel> <channel|>   Indicates a model's internal process.
Note: <|channel> is always followed by the word "thought" when thinking mode is active.

<|turn>system
<|think|><turn|>
<|turn>user
What is the water formula?<turn|>
<|turn>model
<|channel>thought
...
<channel|>The most common interpretation of "the water formula" refers...<turn|>
```

Thinking is a **single control token present or absent in the system turn** — that is literally why only on/off exist and why `low`/`medium` cannot produce graded behaviour. The note's conclusion is right; this is the reason.

**⚠️ ADDITION with build consequences**, verbatim from the same page:

> `Thinking mode is designed to be enabled at the conversation level. This should be consolidated into a single system turn alongside your other system instructions, such as tool definitions.`

So do **not** plan to flip `thinkingLevel` per-request inside one ongoing conversation (e.g. `minimal` for chat turns and `high` for the extraction turn on the same history). Google says it is a conversation-level setting consolidated into the system turn. If LetterLens wants both modes, use **two separate calls with separate histories**, not a mid-thread toggle. The note's build table ("minimal for fast UI paths, high for careful extraction") is fine as long as those are separate requests.

**12. CONFIRMED, with the caveat that half of it is the researcher's inference.** The enum is exact, verbatim:

```
ThinkingLevel
Allow user to specify how much to think using enum instead of integer budget.
Enums
THINKING_LEVEL_UNSPECIFIED   Default value.
MINIMAL                      Little to no thinking.
LOW                          Low thinking level.
MEDIUM                       Medium thinking level.
HIGH                         High thinking level.
```

And the warning, verbatim: `Controls the maximum depth of the model's internal reasoning process before it produces a response. The default value is model-dependent. Refer to the Thinking levels guide for more details. Recommended for Gemini 3 or later models. Use with earlier models results in an error.`

**Caveat:** "the Gemma page **overrides** this for Gemma 4" is the researcher's reading, not doc text. No page says Gemma overrides the reference. What is true is narrower and sufficient: the warning is about *earlier* models, Gemma 4 is not one of them, and the Gemma page shows a working `thinkingLevel` example with the Gemma ID. Treat it as supported; do not quote Google as having said it overrides anything.

Also, `ThinkingConfig`'s full JSON representation is `{ "includeThoughts": boolean, "thinkingBudget": integer, "thinkingLevel": enum (ThinkingLevel) }` — the note omits `includeThoughts` and `thinkingBudget`. `thinkingBudget` is the older integer form; do not mix it with `thinkingLevel`. `includeThoughts` is how you would surface the thought channel in the UI if you ever wanted to.

**13. CONFIRMED, with a factual correction to the sample count.** `streamGenerateContent` on the Gemma page = **0 occurrences** — confirmed independently.

**CORRECTION:** the note says "all **ten** of its REST samples use non-streaming `:generateContent`". My count: the Gemma page contains **7** `curl` calls to `models/gemma-4-26b-a4b-it:generateContent`, plus the Files-API upload `curl`s, for 9 `curl` tokens in total. The figure "ten" is wrong. The substance — **zero streaming samples anywhere on the Gemma page** — is correct and is what matters.

The generic method definition is confirmed verbatim from the reference:

```
Method: models.streamGenerateContent
Endpoint
post https://generativelanguage.googleapis.com/v1beta/{model=models/*}:streamGenerateContent
Generates a streamed response from the model given an input GenerateContentRequest.
```

(`streamGenerateContent` = 8 occurrences on `/api/generate-content`; `gemma` = 0 on that page.) A web search I ran returned a summary asserting "You can use `streamGenerateContent` with Gemma models" — that is a search-engine summarisation artifact, not a doc sentence; the page it cites has zero occurrences of the method. **Not evidence.** Verdict unchanged: **likely works, not documented. Test it.**

**14. PARTIALLY CONFIRMED — one sub-claim is not documented and was labelled "high".**

Confirmed: the non-streaming shape `POST https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent` (7 verbatim occurrences on the Gemma page). Confirmed: the streaming shape, verbatim from https://ai.google.dev/gemini-api/docs/generate-content/text-generation:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:streamGenerateContent?alt=sse" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  --no-buffer \
  -d '{ "contents": [ { "parts": [ { "text": "Explain how AI works" } ] } ] }'
```

`--no-buffer` = 1 occurrence and `alt=sse` = 1 on that page; `alt=sse` = 5 on `/api/generate-content`, 2 on the new text-generation page.

**NOT CONFIRMED — correct this:** the assertion that *"`alt=sse` is required for SSE, otherwise a streamed JSON array is returned"* does **not** appear on any page I fetched. I searched the legacy text-generation page, the new text-generation page and the API reference for `json array`, `server-sent` and `Server Sent` — **zero hits on all three.** The statement is very likely true in practice, but it is **inference presented as documentation at "high" confidence.** Build posture is unaffected — always send `?alt=sse` — but there is no Google page to cite for the "otherwise" half.

**15. CONFIRMED in substance, with corrected counts.** Confirmed: `x-goog-api-key` is the current-docs form — **19 occurrences** on the legacy text-generation page, and it is the form used on the legacy structured-output page, the legacy image-understanding page and the new `/v1beta/interactions` samples. Confirmed: **the Gemma page carries `x-goog-api-key` = 0 occurrences** — its curl samples genuinely ship with no auth at all, so you must add the header yourself. Minimal Gemma call verbatim, auth-free as published:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemma-4-26b-a4b-it:generateContent" \
-H 'Content-Type: application/json' \
-X POST \
-d '{ "contents": [{ "parts":[{"text": "Roses are red..."}] }] }'
```

**CORRECTIONS:** (a) the note says `?key=` appears "6 occurrences" in `/api/generate-content`; my count on that page is **20** occurrences of `key=` and **0** occurrences of `x-goog-api-key` — the reference page uses the query-param form *exclusively*, which is a stronger version of the note's point, not a weaker one. (b) The note's "Both work" is a reasonable inference from Google shipping both forms in current docs, but no page I fetched contains a sentence stating that both are accepted. The recommendation — use the header, keep keys out of URLs and logs — stands and is the right call for LetterLens regardless.

**16. CONFIRMED.** New surface verbatim from https://ai.google.dev/gemini-api/docs/text-generation:

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ "model": "gemini-3.8-flash", "input": "How does AI work?" }'
```

My counts: new text-generation page — `v1beta/interactions` = 12, `:generateContent` = **0**, `gemma` = **0**. New structured-output page — `v1beta/interactions` = 5, `:generateContent` = **0**, `response_format` = 16, `gemma` = **0**.

Page `<title>` values, fetched and confirmed:

```
Structured outputs  |  Gemini Generate Content API (Legacy)  |  Google AI for Developers
Text generation     |  Gemini Generate Content API (Legacy)  |  Google AI for Developers
Image understanding |  Gemini Generate Content API (Legacy)  |  Google AI for Developers
Structured outputs  |  Gemini API  |  Google AI for Developers      <- /docs/structured-output (new)
Text generation     |  Gemini API  |  Google AI for Developers      <- /docs/text-generation (new)
```

Also worth noting for later: the new surface's SDK shape is an `Interactions.Create` call returning an `Interaction` read via `interaction.output_text`, and the docs warn `.output_text does not include earlier text blocks separated by non-text content (such as thoughts, images, audio, or tool calls)`. Irrelevant for Gemma today, but it is where the API is going. **Target `:generateContent` for Gemma. Confirmed.**

**17. CONFIRMED verbatim.** https://ai.google.dev/gemini-api/docs/pricing — the whole page contains **exactly one** case-insensitive occurrence of `gemma` (the block heading), which is consistent with the note. Re-extracted block:

```
Gemma 4
Our lightweight, state-of the art, open model built from the same technology
that powers our Gemini models.
                              Free Tier         Paid Tier, per 1M tokens in USD
Input price                   Free of charge    Not available
Output price                  Free of charge    Not available
Context caching price         Free of charge    Not available
Context caching (storage)     Free of charge    Not available
Tuning price                  Not available     Not available
Grounding with Google Search  Not available     Not available
Used to improve our products  Yes               No
```

Every element of the claim holds, including `Used to improve our products: Yes` on Free Tier, and including the Google-Search `Not available / Not available` that contradicts the Gemma page's working `"tools": [{"googleSearch": {}}]` sample (`googleSearch` = 2 occurrences on the Gemma page). **The contradiction the researcher flagged is real and I reproduce it.** The privacy point is well made and I endorse it: this is a disclosure obligation for an app that reads personal letters, and there is no paid tier to opt out through.

**18. CONFIRMED.** https://ai.google.dev/gemini-api/docs/rate-limits — `gemma` = **0**. Verbatim:

> `Gemini API rate limits` — `Rate limits depend on a variety of factors (such as your usage tier) and can be viewed in Google AI Studio. As your tier and account status change over time, your rate limits will automatically update.` / `Specified rate limits are not guaranteed and actual capacity may vary.`
> `Rate limits are applied per project, not per API key. Requests per day (RPD) quotas reset at midnight Pacific time. Limits vary depending on the specific model being used…`
> `Each model variation has an associated rate limit (requests per minute, RPM). For details on those rate limits, see the AI Studio Rate Limit page.`
> `If you hit a spend-based rate limit, the API returns a 429 RESOURCE_EXHAUSTED error. To resolve this: Wait and retry after a short period. Reduce the rate of expensive requests…`

Spend table confirmed verbatim (`Free N/A / Tier 1 $10 / Tier 2 $50 / Tier 3 $200`, `These limits are evaluated on a rolling 10-minute window`).

**ADDITIONS the note missed, both operationally useful:**
- `Requests per day (RPD) quotas reset at midnight Pacific time` — a demo that burns the daily quota does not recover until 00:00 PT, and with no paid tier there is no billing fix.
- `Priority inference rate limits` — `Priority consumption holds its own rate limits even though consumption is counted towards overall interactive traffic rate limits. Default rate limits are: 0.3x the standard rate limit for each model and tier.`
- There is also a `Batch API rate limits` section — irrelevant to a live demo, but a real escape hatch for bulk letter processing.

**19. CONFIRMED.** https://ai.google.dev/gemini-api/docs/openai — `gemma` = **0**. Opening sentence verbatim: `Gemini models are accessible using the OpenAI libraries (Python and TypeScript / Javascript) along with the REST API, by updating three lines of code and using your Gemini API key. If you aren't already using the OpenAI libraries, we recommend that you call the Gemini API directly.` My counts on that page: `v1beta/openai/` = 43, `Authorization: Bearer` = 13, `x-goog-api-key` = **0**, `tool_choice` = 3, `"stream": true` = 1, `reasoning_effort` = 7. Base URL verbatim: `base_url="https://generativelanguage.googleapis.com/v1beta/openai/"`. All elements of the claim confirmed, including that the auth header on this endpoint is Bearer and **not** `x-goog-api-key`.

**20. CONFIRMED as genuinely unverifiable.** I ran my own search for `"gemma-4-26b-a4b-it" OR "gemma-4-31b-it" generativelanguage openai/chat/completions`. Everything returned was either a localised copy of the same Gemma-on-Gemini-API page (`?hl=de`, `?hl=vi`, `?hl=tr`, `?hl=sq`, `?hl=fa`, `?hl=es-419`) or a third-party host (novita.ai, baseten.co, haimaker.ai) serving the weights behind *its own* OpenAI-compatible API. One search summary asserted the model "is available via OpenAI-compatible APIs" — that is about those third-party gateways, **not** Google's `/v1beta/openai/` endpoint, and is not evidence. The researcher's caution here is exactly right and I could not improve on it. **Unverified. One curl settles it.**

**21. CONFIRMED, with the caveat restated at claim level.** https://ai.google.dev/gemma/docs/capabilities/vision/image, verbatim:

> `OCR (Optical Character Recognition)` — `Models can recognize multilingual texts in the image.`
> `Object Detection` — `Models are trained to detect objects in an image and get their bounding box coordinates. Bounding box coordinates are expressed as normalized values relative to a 1000x1000 grid. You need to descale these coordinates based on your original image size.`

`1000x1000` = 1 occurrence. **Caveat (the note states this in its body but the claim as written drops it):** this page is a Hugging Face `transformers` notebook — `pip install "transformers>=5.10.1"`, `pipeline(task="image-text-to-text", model=MODEL_ID, device_map="auto", dtype="auto")`, with `inline_data`/`inlineData` = 0 and `base64` = 0. It documents **model** capability on local weights, not hosted-endpoint behaviour. Same weights, so the capability transfers; the exact output formatting of a bounding-box prompt through the Gemini API is not documented. For LetterLens, OCR is the relevant half and it is well supported.

**22. CONFIRMED verbatim — but the applicability caveat is the important part, and the note under-weights it.** From https://ai.google.dev/gemini-api/docs/generate-content/image-understanding, both statements found verbatim (at two separate places on the page):

> `Note: Inline image data limits your total request size (text prompts, system instructions, and inline bytes) to 20MB. For larger requests, upload image files using the File API.`
> `Passing inline image data: Ideal for smaller files (total request size less than 20MB, including prompts).`
> `Supported image formats` — `Gemini supports the following image format MIME types: PNG - image/png / JPEG - image/jpeg / WEBP - image/webp / HEIC - image/heic / HEIF - image/heif`

**⚠️ CAVEAT:** this page is titled `Image understanding | Gemini Generate Content API (Legacy)`, its `gemma` count is **0**, and the MIME sentence reads `Gemini supports…`. So the 20MB cap and the five-format list are documented **for Gemini models, on a legacy page** — they are *not* documented as Gemma limits. The claim presents them as applying to Gemma at "high" confidence; for *Gemma specifically* the honest grade is medium-by-inference.

**And the two Google pages do not agree on the format list.** `Blob.mimeType` in the API reference lists a wider set: `image/png, image/jpeg, image/jpg, image/webp, image/heic, image/heif, image/gif, image/avif`. **Send PNG or JPEG and you are inside every list on every page.** Do not build a format-validation allowlist from the five-item list and treat it as authoritative for Gemma.

**23. CONFIRMED.** Verbatim from the vision page, and I extracted every `google/gemma-4-*` string on it:

```python
MODEL_ID = "google/gemma-4-E2B-it" # @param ["google/gemma-4-E2B-it", "google/gemma-4-E4B-it", "google/gemma-4-12B-it", "google/gemma-4-31B-it", "google/gemma-4-26B-A4B-it"]
```

Exact set found: `google/gemma-4-E2B-it`, `google/gemma-4-E4B-it`, `google/gemma-4-12B-it`, `google/gemma-4-31B-it`, `google/gemma-4-26B-A4B-it`. Five open sizes, capitalised; two hosted, lowercased with `-it`. **The casing difference is real — `gemma-4-26B-A4B-it` is the Hugging Face id and `gemma-4-26b-a4b-it` is the Gemini API id. Do not cross them.**

### What the researcher missed that the build will need

1. **`https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4` is absent from the note's source index, and it is the most build-relevant page they skipped.** It gives Gemma 4's actual control tokens (`<|turn>`/`<turn|>`, `system`/`user`/`model`, `<|image|>`, `<|audio|>`, `<|think|>`, `<|channel>`/`<channel|>`, `<|tool>`, `<|tool_call>`, `<|tool_response>`, `<|"|>`). Three consequences: it independently proves the native `system` role; it explains *why* thinking is binary; and it shows there is no schema/JSON token, the strongest available evidence that structured output is not a Gemma-trained capability.

2. **Thinking is a conversation-level setting, not a per-request dial.** Verbatim: `Thinking mode is designed to be enabled at the conversation level. This should be consolidated into a single system turn alongside your other system instructions, such as tool definitions.` The note's build table implies you can flip `minimal`/`high` freely. Use separate calls with separate histories instead.

3. **`gemma-4-31b-it` is a documented ID with zero worked examples.** It appears exactly once on the entire Gemma page. Falling back to 31B if the 26B A4B is rate-limited is reasonable but entirely unexemplified — expect to port every sample yourself, and expect the dense 31B to be slower than the ~3.8B-active MoE.

4. **The two Google pages disagree on supported image MIME types** (five on the legacy image guide vs eight on the `Blob` reference, which adds `image/jpg`, `image/gif`, `image/avif`). Neither list is stated for Gemma. Send PNG/JPEG.

5. **`TextResponseFormat.mimeType` is a proto enum (`APPLICATION_JSON`/`TEXT_PLAIN`), and `text/x.enum` is not one of its values.** Enum-constrained output lives only on the deprecated `responseMimeType`. The note's §4.3 shape is right but this distinction is missing, and it would bite anyone trying to get a single-label classification out of the new field.

6. **`RPD` resets at midnight Pacific**, and **priority inference runs at 0.3x the standard limit**. Both from the rate-limits page, both absent from the note. There is a **Batch API** with its own limits if bulk letter processing is ever needed.

7. **`Blob.displayName` exists** — useful if you send several letter pages inline in one request and want the model to refer to them by name.

8. **E2B/E4B are 128K context, not 256K.** The note's "256K" generalisation holds only for 12B Unified, 26B A4B and 31B. Irrelevant for the hosted pair, but do not repeat it as a family-wide fact.

9. **Gemma 4 turn tokens differ from Gemma 3's** (`<|turn>` vs `<start_of_turn>`). Only matters if local weights ever enter the picture; the Gemini API handles templating.

### Things in the note that should be softened before anyone codes from it

- Claim 14's "`alt=sse` is required, otherwise a streamed JSON array is returned" — correct practice, **undocumented** on any page fetched in either pass. Graded "high"; should be "high on the endpoint shape, inference on the fallback behaviour".
- Claim 15's occurrence counts (`key=` is 20 on the reference page, not 6) and its "Both work" — the latter is a sound inference from Google shipping both forms, not a quoted statement.
- Claim 12's "the Gemma page overrides this" — no page says that. The working example is sufficient; do not attribute an override to Google.
- Claim 13's "ten REST samples" — it is 7 `:generateContent` curls. The zero-streaming finding is unaffected.
- Claim 22's confidence **for Gemma** — the 20MB cap and MIME list are Gemini-page facts on a legacy page with zero Gemma mentions.
- §3's benchmark table is fine but note the 12B Unified column exists too (MMLU Pro 77.2%), which the note's three-column excerpt drops.

### Net

23 claims checked against pages I fetched myself. **18 confirmed outright; 4 confirmed with corrections (9, 13, 15, 22); 1 partially confirmed with an undocumented sub-claim (14). Zero refuted.** No hallucinated model IDs, package names or field names anywhere in the note. The three blockers — structured output unverified, streaming unverified, no paid tier — all survive adversarial re-checking, as does the inline-image-transport blocker.

**The build can proceed on `gemma-4-26b-a4b-it` via `POST /v1beta/models/gemma-4-26b-a4b-it:generateContent` with the `x-goog-api-key` header, function calling for typed output, `systemInstruction` passed directly, and `thinkingLevel` of `high` or `minimal` set once per conversation rather than per request.** The §9 open questions are the right five minutes of curl to spend first; add a seventh — if you test `responseFormat` at all, try `"mimeType": "APPLICATION_JSON"` as well as `"application/json"` before concluding it is unsupported.

**Pages I fetched in this pass (all HTTP 200):** gemma_on_gemini_api, releases, model_card_4, prompt-formatting-gemma4 *(new)*, capabilities/vision/image, gemini-api/docs/models, pricing, rate-limits, openai, api/generate-content, structured-output (new + legacy), text-generation (new + legacy), generate-content/image-understanding, philschmid.de/gemma-4-gemini-api.
