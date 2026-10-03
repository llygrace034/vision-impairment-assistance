# 07 — Gemini API: image input, structured JSON output, function calling (exact REST payloads)

Research date: **2026-10-03**. All facts below come from pages fetched in this task; each section carries its
source URL and the doc page's own "Last updated" date where available. Anything I could not confirm is
explicitly labelled **UNCONFIRMED**.

---

## 0. THE BIG THING TO KNOW FIRST: there are now TWO APIs

Google has shipped a new **Interactions API** and has re-labelled the whole `generateContent` doc tree as
"**Gemini Generate Content API (Legacy)**" (that string is the `<title>` of every `/generate-content/...` page).

| | Legacy | Current / recommended |
|---|---|---|
| Endpoint | `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | `POST https://generativelanguage.googleapis.com/v1beta/interactions` |
| Streaming | `:streamGenerateContent?alt=sse` | same `/interactions` endpoint with `"stream": true` |
| Request root | `contents[].parts[]` | `input` (string, or array of typed blocks) |
| Response root | `candidates[0].content.parts[0].text` | `steps[]` (find the `model_output` step) / `interaction.output_text` |
| Python call | `client.models.generate_content(...)` | `client.interactions.create(...)` |

Verbatim from <https://ai.google.dev/gemini-api/docs/migrate-to-interactions> (fetched 2026-10-03):

> This guide helps you migrate from the generateContent API to the Interactions API.
> The Interactions API is our simplest and best way to build with Gemini models and agents.
> **While generateContent remains fully supported, we recommend the Interactions API for all new development.**

**Recommendation for LetterLens:** `generateContent` is explicitly "fully supported", and it is the API shape
this project's spec assumes, so building on `generateContent` is safe. But know that (a) its docs are marked
Legacy, (b) `generationConfig.responseSchema` is now formally **deprecated** (see §3), and (c) every doc code
sample now uses `gemini-3.8-flash`.

There is also a documented breaking-change page: `/gemini-api/docs/interactions-breaking-changes-may-2026`
(listed in site nav; not fetched in this task — **UNCONFIRMED** contents).

### Version-path inconsistency in the docs (real, worth knowing)
- `structured-output`, `function-calling`, `streaming`, `interactions-overview` all use **`/v1beta/interactions`**.
- `migrate-to-interactions` uses **`/v1beta2/interactions`** in every curl block.

Counts across pages fetched today: 9 occurrences of `v1beta2` (all on the migrate page) vs `v1beta/interactions`
on 5 other pages. Treat **`/v1beta/interactions`** as canonical; the migrate page looks stale.

---

## 1. Models

From <https://ai.google.dev/gemini-api/docs/models> (fetched 2026-10-03), the model IDs present on the page:

```
gemini-3.8-flash            <- used in ~all current doc samples
gemini-3.8-flash-lite-tts
gemini-3.8-flash-tts
gemini-3.8-live
gemini-3.8-live-extended-thinking
gemini-3.7-flash
gemini-3.6-flash
gemini-3.5-flash
gemini-3.5-flash-lite
gemini-3.5-transcribe / gemini-3.5-transcribe-live / gemini-3.5-live-translate-preview
gemini-3.1-pro-preview
gemini-3.1-flash-lite  / gemini-3.1-flash-lite-preview
gemini-3.1-flash-image / gemini-3.1-flash-lite-image / gemini-3.1-flash-live-preview / gemini-3.1-flash-tts-preview
gemini-3-pro-preview / gemini-3-pro-image / gemini-3-flash-preview
gemini-2.5-pro / gemini-2.5-flash / gemini-2.5-flash-lite / gemini-2.5-flash-image
gemini-2.5-computer-use-preview-10-2025 / gemini-2.5-flash-native-audio-preview-12-2025
gemini-2.5-flash-preview-tts / gemini-2.5-pro-preview-tts / gemini-2.5-flash-preview-09-2025
gemini-2.0-flash / gemini-2.0-flash-lite
```

Default pick for LetterLens: **`gemini-3.8-flash`** (what every current sample uses).

### Auth
From <https://ai.google.dev/gemini-api/docs/generate-content/api-key> (fetched 2026-10-03):

> Set the environment variable `GEMINI_API_KEY` or `GOOGLE_API_KEY`. … If both are set, `GOOGLE_API_KEY` takes precedence.

REST header used in every sample: `-H "x-goog-api-key: $GEMINI_API_KEY"`
Explicit Python override: `client = genai.Client(api_key="YOUR_API_KEY")`

---

## 2. Image input — exact REST payload

Source: <https://ai.google.dev/gemini-api/docs/generate-content/image-understanding> (page says "Last updated 2026-09-04 UTC")

> You can provide images as input to Gemini using two methods:
> - Passing inline image data: Ideal for smaller files (total request size less than 20MB, including prompts).
> - Uploading images using the File API: Recommended for larger files or for reusing images across multiple requests.

### 2.1 Inline image, verbatim REST (legacy generateContent)

```bash
IMG_PATH="/path/to/your/image1.jpg"

if [[ "$(base64 --version 2>&1)" = *"FreeBSD"* ]]; then
  B64FLAGS="--input"
else
  B64FLAGS="-w0"
fi

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
}' 2> /dev/null
```

Notes that matter:
- REST field name is **snake_case `inline_data` / `mime_type` / `data`**. The JS SDK uses camelCase
  `inlineData` / `mimeType`. Both spellings exist in the docs for their respective surfaces; the raw REST
  examples consistently use snake_case. (Proto JSON accepts either casing in general, but copy the doc's
  snake_case for REST to be safe.)
- Base64 must be **unwrapped / no newlines** — that is exactly what `base64 -w0` (GNU) / `base64 --input`
  (FreeBSD) / `base64 -b 0` (macOS) in the doc samples is for. No `data:` URI prefix — raw base64 only.
- Place the **text part after the image part** for a single image. Verbatim tip from the page:
  > When using a single image with text, place the text prompt after the image part in the contents array.

### 2.2 Same shape, from the text-generation page (clean, no shell interpolation)

Source: <https://ai.google.dev/gemini-api/docs/generate-content/text-generation> ("Last updated 2026-09-17 UTC")

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
            "data": "/9j/4AAQSkZJRgABAQ... (base64-encoded image)"
            }
        },
        {"text": "What is in this picture?"},
      ]
    }]
  }'
```

### 2.3 Supported image MIME types (verbatim list)

```
PNG  - image/png
JPEG - image/jpeg
WEBP - image/webp
HEIC - image/heic
HEIF - image/heif
```

### 2.4 Size threshold / Files API

> **Note:** Inline image data limits your total request size (text prompts, system instructions, and inline
> bytes) to 20MB. For larger requests, upload image files using the File API.
> Files API is also more efficient for scenarios that use the same image repeatedly.

The 20MB ceiling is the **whole request**, not the image — and base64 inflates bytes by ~4/3, so a ~14–15MB
original JPEG is already at the limit. For LetterLens (photos of letters from phone cameras) this is the
relevant rule: downscale/compress client-side, or switch to the Files API.

### 2.5 Files API part shape (verbatim REST)

```bash
# resumable upload, start
curl "https://generativelanguage.googleapis.com/upload/v1beta/files" \
  -D upload-header.tmp \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Header-Content-Type: ${MIME_TYPE}" \
  -H "Content-Type: application/json" \
  -d "{'file': {'display_name': '${DISPLAY_NAME}'}}" 2> /dev/null

upload_url=$(grep -i "x-goog-upload-url: " "${tmp_header_file}" | cut -d" " -f2 | tr -d "\r")

# Upload the actual bytes.
curl "${upload_url}" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Length: ${NUM_BYTES}" \
  -H "X-Goog-Upload-Offset: 0" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  --data-binary "@${IMAGE_PATH}" 2> /dev/null > file_info.json

file_uri=$(jq -r ".file.uri" file_info.json)

# Now generate content using that file
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
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

So the two part variants are **`inline_data{mime_type,data}`** and **`file_data{mime_type,file_uri}`**.

### 2.6 Limits and token cost (verbatim)

> **File limit** — Gemini models support a maximum of 3,600 image files per request.
>
> **Token calculation** — 258 tokens if both dimensions <= 384 pixels. Larger images are tiled into 768x768
> pixel tiles, each costing 258 tokens. A rough formula for calculating the number of tiles is as follows:
> Calculate the crop unit size which is roughly: `floor(min(width, height) / 1.5)`. Divide each dimension by
> the crop unit size and multiply together to get the number of tiles. For example, for an image of dimensions
> 960x540 would have a crop unit size of 360. Divide each dimension by 360 and the number of tile is 3 * 2 = 6.
>
> **Media resolution** — Gemini 3 introduces granular control over multimodal vision processing with the
> `media_resolution` parameter. The `media_resolution` parameter determines the maximum number of tokens
> allocated per input image or video frame. Higher resolutions improve the model's ability to read fine text or
> identify small details, but increase token usage and latency.

`mediaResolution` lives on `generationConfig` (`"mediaResolution": enum (MediaResolution)` — confirmed in the
GenerationConfig JSON representation at <https://ai.google.dev/api/generate-content>). For LetterLens
(reading dense printed text in a photographed letter) **this is the knob to raise**. The exact enum values are
on `/gemini-api/docs/generate-content/media-resolution`, which I did **not** fetch — **UNCONFIRMED**.

Best-practice bullets, verbatim:
> Verify that images are correctly rotated. / Use clear, non-blurry images. / When using a single image with
> text, place the text prompt after the image part in the contents array.

### 2.7 Python SDK, image input (verbatim)

```python
from google import genai
from google.genai import types

with open('path/to/small-sample.jpg', 'rb') as f:
    image_bytes = f.read()

client = genai.Client()
response = client.models.generate_content(
  model='gemini-3.8-flash',
  contents=[
    types.Part.from_bytes(
      data=image_bytes,
      mime_type='image/jpeg',
    ),
    'Caption this image.'
  ]
)
print(response.text)
```

Files API variant (verbatim):

```python
from google import genai

client = genai.Client()
my_file = client.files.upload(file="path/to/sample.jpg")

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=[my_file, "Caption this image."],
)
print(response.text)
```

### 2.8 Image input on the Interactions API (for reference)

Source: <https://ai.google.dev/gemini-api/docs/migrate-to-interactions>

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta2/interactions" \
-H "Content-Type: application/json" \
-H "x-goog-api-key: $GEMINI_API_KEY" \
-d '{
    "model": "gemini-3.8-flash",
    "input": [
        {
            "type": "image",
            "mime_type": "image/jpeg",
            "data": "..."
        },
        {
            "type": "text",
            "text": "Describe this image."
        }
    ]
}'
```

Response (verbatim):

```json
{
  "id": "int_multimodal",
  "steps": [
    {
      "type": "user_input",
      "status": "done",
      "content": [
        { "type": "image", "mime_type": "image/jpeg", "data": "..." },
        { "type": "text", "text": "Describe this image." }
      ]
    },
    {
      "type": "model_output",
      "status": "done",
      "content": [
        { "type": "text", "text": "This is a picture of a beautiful sunset over the mountains." }
      ]
    }
  ]
}
```

Python (verbatim):

```python
import base64
from google import genai

client = genai.Client()
with open("sample.jpg", "rb") as f:
    image_bytes = f.read()
image_b64 = base64.b64encode(image_bytes).decode("utf-8")

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {
            "type": "image",
            "mime_type": "image/jpeg",
            "data": image_b64,
        },
        {"type": "text", "text": "Describe this image."},
    ],
)
print(interaction.output_text)
```

(Note `/v1beta2/` here — see §0; prefer `/v1beta/interactions`.)

---

## 3. Structured JSON output — the field names CHANGED

Sources:
- Legacy: <https://ai.google.dev/gemini-api/docs/generate-content/structured-output> ("Last updated 2026-09-02 UTC")
- Current: <https://ai.google.dev/gemini-api/docs/structured-output>
- Reference: <https://ai.google.dev/api/generate-content> (GenerationConfig / ResponseFormatConfig / TextResponseFormat / Schema)

### 3.1 ⚠️ `responseSchema` is DEPRECATED

Verbatim from the GenerationConfig reference at <https://ai.google.dev/api/generate-content>:

> `responseMimeType` — `string` — Optional. MIME type of the generated candidate text. Supported MIME types
> are: `text/plain`: (default) Text output. `application/json`: JSON response in the response candidates.
> `text/x.enum`: ENUM as a string response in the response candidates.
>
> `responseSchema` **(deprecated)** — `object (Schema)` — *This item is deprecated!* Optional. Output schema of
> the generated candidate text. Schemas must be a subset of the OpenAPI schema and can be objects, primitives
> or arrays. If set, a compatible `responseMimeType` must also be set. Compatible MIME types:
> `application/json`: Schema for JSON response. **Deprecated. Use `responseFormat` instead.**
>
> `_responseJsonSchema` **(deprecated)** — *This item is deprecated!* … **Deprecated. Use `responseFormat` instead.**
>
> `responseFormat` — `object (ResponseFormatConfig)` — Optional. Configuration for the response output format.
> Allows specifying output configuration per modality (text, audio, image) in a flat structure.

`responseMimeType` itself is **not** marked deprecated. So:
- `generationConfig.responseMimeType = "application/json"` — **still valid, not deprecated.** ✅
- `generationConfig.responseSchema = {...}` — **still accepted but formally deprecated.** ⚠️
- The non-deprecated replacement is `generationConfig.responseFormat.text.{mimeType,schema}`.

### 3.2 Current legacy-API REST payload (what the docs show TODAY)

Verbatim from `/gemini-api/docs/generate-content/structured-output`:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -X POST \
    -d '{
      "contents": [{
        "parts":[
          { "text": "Please extract the recipe from the following text. ..." }
        ]
      }],
      "generationConfig": {
        "responseFormat": {
          "text": {
            "mimeType": "application/json",
            "schema": {
              "type": "object",
              "properties": {
                "recipe_name": { "type": "string", "description": "The name of the recipe." },
                "prep_time_minutes": { "type": "integer", "description": "Optional time in minutes to prepare the recipe." },
                "ingredients": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "name": { "type": "string", "description": "Name of the ingredient."},
                      "quantity": { "type": "string", "description": "Quantity of the ingredient, including units."}
                    },
                    "required": ["name", "quantity"]
                  }
                },
                "instructions": { "type": "array", "items": { "type": "string" } }
              },
              "required": ["recipe_name", "ingredients", "instructions"]
            }
          }
        }
      }
    }'
```

*(The doc's own curl block has mismatched braces around `required` — the brace nesting above is the corrected
form that matches the Go/Python samples on the same page. Flagged so nobody copy-pastes a broken payload.)*

Note the **casing split**: inside `generationConfig` it is camelCase `responseFormat` / `mimeType`; the
Interactions API top-level field is snake_case `response_format` / `mime_type`.

### 3.3 Reference shapes for `responseFormat`

Verbatim from <https://ai.google.dev/api/generate-content>:

```
ResponseFormatConfig
{
  "text":  { object (TextResponseFormat) },
  "audio": { object (AudioResponseFormat) },
  "image": { object (ImageResponseFormat) }
}

TextResponseFormat
{
  "mimeType": enum (MimeType),
  "schema": value
}
```
> `mimeType` — `enum (MimeType)` — Optional. The MIME type of the text output.
> `schema` — `value` — Optional. The JSON schema that the output should conform to. **Only applicable when
> `mimeType` is `APPLICATION_JSON`.**
>
> `MimeType` enums: `MIME_TYPE_UNSPECIFIED`, `APPLICATION_JSON`, `TEXT_PLAIN`
> (REST samples pass the string `"application/json"`.)

### 3.4 Supported JSON-Schema subset (verbatim, current legacy page)

> To generate a JSON object, set the `response_format` in the generation configuration. The schema must be a
> valid JSON Schema that describes the desired output format. The model will then generate a response that is a
> syntactically valid JSON string matching the provided schema. **When using structured outputs, the model will
> produce outputs in the same order as the keys in the schema.**
>
> Gemini's structured output mode supports a subset of the JSON Schema specification.
>
> The following values of `type` are supported:
> - `string`: For text.
> - `number`: For floating-point numbers.
> - `integer`: For whole numbers.
> - `boolean`: For true/false values.
> - `object`: For structured data with key-value pairs.
> - `array`: For lists of items.
> - `null`: To allow a property to be null, include "null" in the type array (e.g., `{"type": ["string", "null"]}`).
>
> These descriptive properties help guide the model:
> - `title`: A short description of a property.
> - `description`: A longer and more detailed description of a property.
>
> **Type-specific properties**
> For `object` values: `properties`, `required`, `additionalProperties` (Controls whether properties not listed
> in `properties` are allowed. Can be a boolean or a schema.)
> For `string` values: `enum` (Lists a specific set of possible strings for classification tasks),
> `format` (Specifies a syntax for the string, such as `date-time`, `date`, `time`).
> For `number` and `integer` values: `enum`, `minimum` (inclusive), `maximum` (inclusive).
> For `array` values: `items`, `prefixItems` (tuple-like structures), `minItems`, `maxItems`.

**Answers to the spec's specific questions:**
- `type`, `properties`, `required`, `items`, `enum` — ✅ all supported, confirmed verbatim.
- **`nullable` — NOT in the current supported list.** The documented way is `{"type": ["string", "null"]}`.
  (`nullable` *does* still exist as a field on the deprecated `Schema` proto: *"`nullable` — `boolean` —
  Optional. Indicates if the value may be null."* — <https://ai.google.dev/api/generate-content>. So it works on
  the `responseSchema` path only. Don't use it with `responseFormat.text.schema`.)
- **`propertyOrdering` — NOT needed on modern models.** Verbatim: *"When using structured outputs, the model
  will produce outputs in the same order as the keys in the schema."* The only place it is required:
  > `*` Note that Gemini 2.0 requires an explicit `propertyOrdering` list within the JSON input to define the
  > preferred structure.
  It is still documented on the `Schema` proto: *"`propertyOrdering[]` — `string` — Optional. The order of the
  properties. Not a standard field in open api spec."*

### 3.5 Model support table (verbatim)

```
Gemini 3.1 Flash-Lite          ✔️
Gemini 3.1 Pro Preview         ✔️
Gemini 3.5 Flash               ✔️
Gemini 3.1 Flash-Lite Preview  ✔️
Gemini 2.5 Pro                 ✔️
Gemini 2.5 Flash               ✔️
Gemini 2.5 Flash-Lite          ✔️
Gemini 2.0 Flash               ✔️*
Gemini 2.0 Flash-Lite          ✔️*
```
(The table predates 3.6/3.7/3.8 but the 3.8 samples on the same page use structured output, so 3.8-flash
clearly supports it.)

### 3.6 Limitations (verbatim)

> **Schema subset:** Not all features of the JSON Schema specification are supported. **The model ignores
> unsupported properties.**
> **Schema complexity:** The API may reject very large or deeply nested schemas. If you encounter errors, try
> simplifying your schema by shortening property names, reducing nesting, or limiting the number of constraints.

And the validation warning, verbatim:
> **Validation:** While structured output guarantees syntactically correct JSON, it does not guarantee the
> values are semantically correct. Always validate the final output in your application code before using it.

### 3.7 Does structured output work with image input? — **PARTIALLY CONFIRMED (medium confidence)**

I could **not** find a single doc page with a verbatim example combining an image part and
`responseFormat`/`responseSchema` in one request. What I can confirm:
- `responseFormat` lives in `generationConfig`, which is orthogonal to `contents[].parts[]`. Nothing in the
  schema docs conditions it on input modality.
- The structured-output page shows it composing with *other* request features — there is a
  "Structured outputs with tools" section that combines `googleSearch` + `urlContext` + `responseFormat`.
- <https://ai.google.dev/gemini-api/docs/generate-content/document-processing> lists, as a capability of
  document (PDF/image) input: *"Extract information into structured output formats."*
- The structured-output page's own index has sections: Recipe Extractor, Content Moderation, Recursive
  Structures, Streaming, Structured outputs with tools — **no image/multimodal section**.

**Verdict:** very likely works (and is the core LetterLens pattern), but treat it as **unverified by a doc
example**. Smoke-test it on day 1 with a real photo before building on it.

### 3.8 Structured outputs with tools, verbatim REST (proves composability)

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [{ "parts": [{"text": "Search for all details for the latest Euro."}] }],
    "tools": [
      {"googleSearch": {}},
      {"urlContext": {}}
    ],
    "generationConfig": {
        "responseFormat": {
          "text": {
            "mimeType": "application/json",
            "schema": {
              "type": "object",
              "properties": {
                "winner": {"type": "string", "description": "The name of the winner."},
                "final_match_score": {"type": "string", "description": "The final score."},
                "scorers": {"type": "array", "items": {"type": "string"}, "description": "The name of the scorer."}
              },
              "required": ["winner", "final_match_score", "scorers"]
            }
          }
        }
    }
  }'
```

### 3.9 Python SDK, structured output (verbatim)

Legacy `generate_content` form — note `config={"response_format": {"text": {...}}}` (snake_case in Python):

```python
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional

class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient.")
    quantity: str = Field(description="Quantity of the ingredient, including units.")

class Recipe(BaseModel):
    recipe_name: str = Field(description="The name of the recipe.")
    prep_time_minutes: Optional[int] = Field(description="Optional time in minutes to prepare the recipe.")
    ingredients: List[Ingredient]
    instructions: List[str]

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=prompt,
    config={
        "response_format": {"text": {"mime_type": "application/json", "schema": Recipe.model_json_schema()}},
    },
)
recipe = Recipe.model_validate_json(response.text)
print(recipe)
```

Interactions form (verbatim from `/gemini-api/docs/structured-output`):

```python
client = genai.Client()
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": Recipe.model_json_schema()
    },
)
```

Interactions REST (verbatim) — note `response_format` is **top-level**, with a `"type": "text"` discriminator:

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
    -H "x-goog-api-key: $GEMINI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d '{
      "model": "gemini-3.8-flash",
      "input": "Please extract the recipe from the following text...",
      "response_format": {
        "type": "text",
        "mime_type": "application/json",
        "schema": {
          "type": "object",
          "properties": {
            "recipe_name": { "type": "string", "description": "The name of the recipe." },
            "prep_time_minutes": { "type": "integer", "description": "Optional time in minutes to prepare the recipe." },
            "ingredients": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "name": { "type": "string", "description": "Name of the ingredient."},
                  "quantity": { "type": "string", "description": "Quantity of the ingredient, including units."}
                },
                "required": ["name", "quantity"]
              }
            },
            "instructions": { "type": "array", "items": { "type": "string" } }
          },
          "required": ["recipe_name", "ingredients", "instructions"]
        }
      }
    }'
```

JS SDK uses camelCase: `config: { responseFormat: { text: { mimeType: "application/json", schema: zodToJsonSchema(recipeSchema) } } }`

### 3.10 Structured outputs vs function calling (verbatim)

> **Structured Outputs** — Formatting the final response to the user. Use this when you want the model's answer
> to be in a specific format (e.g., extracting data from a document to save to a database).
> **Function Calling** — Taking action during the conversation. Use this when the model needs to ask you to
> perform a task (e.g., "get current weather") before it can provide a final answer.

For LetterLens (extract fields from a letter image → JSON), **structured output is the right tool**, not
function calling.

---

## 4. Function calling — exact request/response

Source: <https://ai.google.dev/gemini-api/docs/generate-content/function-calling> (legacy / generateContent)
and <https://ai.google.dev/gemini-api/docs/function-calling> (Interactions).

### 4.1 Legacy REST request, verbatim

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [
      {
        "role": "user",
        "parts": [
          { "text": "Schedule a meeting with Bob and Alice for 03/27/2025 at 10:00 AM about the Q3 planning." }
        ]
      }
    ],
    "tools": [
      {
        "functionDeclarations": [
          {
            "name": "schedule_meeting",
            "description": "Schedules a meeting with specified attendees at a given time and date.",
            "parameters": {
              "type": "object",
              "properties": {
                "attendees": {
                  "type": "array",
                  "items": {"type": "string"},
                  "description": "List of people attending the meeting."
                },
                "date": { "type": "string", "description": "Date of the meeting (e.g., '2024-07-29')" },
                "time": { "type": "string", "description": "Time of the meeting (e.g., '15:00')" },
                "topic": { "type": "string", "description": "The subject or topic of the meeting." }
              },
              "required": ["attendees", "date", "time", "topic"]
            }
          }
        ]
      }
    ]
  }'
```

So: **`tools[].functionDeclarations[]`** (camelCase even in REST here), each with `name`, `description`,
`parameters` (an OpenAPI-subset object schema), and `parameters.required[]`.

### 4.2 Function declaration fields (verbatim)

> When you implement function calling in a prompt, you create a `tools` object, which contains one or more
> function declarations. You define functions using JSON, specifically with a select subset of the OpenAPI
> schema format. A single function declaration can include the following parameters:
> - `name` (string): A unique name for the function (`get_weather_forecast`, `send_email`). Use descriptive
>   names without spaces or special characters (use underscores or camelCase).
> - `description` (string): A clear and detailed explanation of the function's purpose and capabilities. This is
>   crucial for the model to understand when to use the function.
> - `parameters` (object): Defines the input parameters the function expects.
>   - `type` (string): Specifies the overall data type, such as `object`.
>   - `properties` (object): Lists individual parameters, each with: `type` (string), `description` (string),
>     `enum` (array, optional) — "If the parameter values are from a fixed set, use "enum" to list the allowed
>     values instead of just describing them in the description. This improves accuracy
>     (`"enum": ["daylight", "cool", "warm"]`)."
>   - `required` (array): An array of strings listing the parameter names that are mandatory.
>
> You can also construct FunctionDeclarations from Python functions directly using
> `types.FunctionDeclaration.from_callable(client=client, callable=your_function)`.

### 4.3 Response shape — `functionCall`

> The model then returns a `functionCall` object in an OpenAPI compatible schema specifying how to call one or
> more of the declared functions in order to respond to the user's question.

Verbatim printed objects:

```
# Python repr
id='8f2b1a3c' args={'color_temp': 'warm', 'brightness': 25} name='set_light_values'
```
```js
// JavaScript
{
  id: '8f2b1a3c',
  name: 'set_light_values',
  args: { brightness: 25, color_temp: 'warm' }
}
```
```go
// Go
&{ID:8f2b1a3c Args:map[brightness:25 color_temp:warm] Name:set_light_values}
```

Wire path confirmed by the doc's own Python/JS code: `response.candidates[0].content.parts[0].function_call`
(Python snake_case) → on the wire `candidates[].content.parts[].functionCall.{id,name,args}`.

⚠️ **New in Gemini 3 — there is now an `id` on every function call, and it is mandatory to echo it back.** Verbatim:

> `*` **Always map function IDs:** Gemini 3 now always returns a unique `id` with every `functionCall`.
> Include this exact `id` in your `functionResponse` so the model can accurately map your result back to the
> original request.

and for parallel calls:

> When the model initiates multiple function calls in a single turn, you don't need to return the
> `function_result` objects in the same order that the `function_call` objects were received. The Gemini API
> maps each result back to its corresponding call using the `id` from the model's output.

Also note the doc's own comment: `# Extract tool call details, it may not be in the first part.`
— **do not hardcode `parts[0]`**; scan all parts for one carrying `functionCall`.

### 4.4 Returning the result — `functionResponse`

```js
// Create a function response part
const function_response_part = {
  name: tool_call.name,
  response: { result },
  id: tool_call.id
}
// Append function call and result of the function execution to contents
contents.push(response.candidates[0].content);
contents.push({ role: 'user', parts: [{ functionResponse: function_response_part }] });
```

So the wire part is `{"functionResponse": {"id": ..., "name": ..., "response": {...}}}` sent with
`"role": "user"`, and the model's own `content` (the whole thing, unmodified) must be appended first.

### 4.5 FORCED function calling — `toolConfig.functionCallingConfig`

Verbatim, the four modes:

> The Gemini API lets you control how the model uses the provided tools (function declarations). Specifically,
> you can set the `mode` within the `.function_calling_config`.
>
> - **`VALIDATED`**: Default mode for tool combination (when built-in tools or structured outputs also enabled).
>   The model is constrained to predict either function calls or natural language, and ensures function schema
>   adherence. If `allowed_function_names` is not provided, the model picks from all of the available function
>   declarations. If `allowed_function_names` is provided, the model picks from the set of allowed functions.
>   This mode reduces malformed function calls (compared to AUTO mode).
> - **`AUTO`**: Default mode when only `function_declarations` tool enabled. The model decides whether to
>   generate a natural language response or suggest a function call based on the prompt and context.
> - **`ANY`**: The model is constrained to always predict a function call and ensures function schema adherence.
>   If `allowed_function_names` is not specified, the model can choose from any of the provided function
>   declarations. If `allowed_function_names` is provided as a list, the model can only choose from the
>   functions in that list. Use this mode when you require a function call response to every prompt (if applicable).
> - **`NONE`**: The model is prohibited from making function calls. This is equivalent to sending a request
>   without any function declarations. Use this to temporarily disable function calling without removing your
>   tool definitions.

**There are FOUR modes, not three — `VALIDATED` is new and is the default whenever you combine function
declarations with built-in tools or structured outputs.**

Python (verbatim):

```python
from google.genai import types

# Configure function calling mode
tool_config = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode="ANY", allowed_function_names=["get_current_temperature"]
    )
)

# Create the generation config
config = types.GenerateContentConfig(
    tools=[tools],  # not defined here.
    tool_config=tool_config,
)
```

JS (verbatim):

```js
import { FunctionCallingConfigMode } from '@google/genai';
const toolConfig = {
  functionCallingConfig: {
    mode: FunctionCallingConfigMode.ANY,
    allowedFunctionNames: ['get_current_temperature']
  }
};
const config = {
  tools: tools, // not defined here.
  toolConfig: toolConfig,
};
```

Go (verbatim): `genai.FunctionCallingConfigModeAny`, `AllowedFunctionNames: []string{"get_current_temperature"}`.

**REST equivalent — NOT shown verbatim anywhere on the legacy function-calling page.** By the SDK-to-REST
naming convention (camelCase in the JSON body, as `functionDeclarations` already shows) it is:

```json
{
  "contents": [ ... ],
  "tools": [ { "functionDeclarations": [ ... ] } ],
  "toolConfig": {
    "functionCallingConfig": {
      "mode": "ANY",
      "allowedFunctionNames": ["get_current_temperature"]
    }
  }
}
```

**Confidence: medium.** The field names `toolConfig`, `functionCallingConfig`, `mode`,
`allowedFunctionNames`/`allowed_function_names` are all documented; the exact REST JSON block is my
reconstruction, not a verbatim doc sample. Verify with one curl before relying on it.

### 4.6 Thought signatures — a real multi-turn trap for Gemini 3

Verbatim:

> Because the Gemini API is stateless, models use thought signatures to maintain context across multi-turn
> conversations. … If you modify the conversation history manually, instead of sending the complete previous
> response you must correctly handle the `thought_signature` included in the model's turn. Follow these rules
> to ensure the model's context is preserved:
> - Always send the `thought_signature` back to the model inside its original `Part`.
> - Always include the exact `id` from the `function_call` in your `function_response` so the API can map the
>   result to the correct request.
> - Don't merge a `Part` containing a signature with one that does not. This breaks the positional context of
>   the thought.
> - Don't combine two `Part`s that both contain signatures, as the signature strings cannot be merged.
>
> In Gemini 3, any `Part` of a model response may contain a thought signature. While we generally recommend
> returning signatures from all `Part` types, **passing back thought signatures is mandatory for function
> calling.** Unless you are manipulating conversation history manually, the Google GenAI SDK will handle thought
> signatures automatically.

Inspecting one (verbatim Python):

```python
import base64
# The signature is attached to the response part containing the function call
part = response.candidates[0].content.parts[0]
if part.thought_signature:
  print(base64.b64encode(part.thought_signature).decode("utf-8"))
```

A missing signature has its own finish reason: **`MISSING_THOUGHT_SIGNATURE`** — "Request has at least one
thought signature missing." (see §5). **If LetterLens hand-rolls REST function calling across turns, this is
the #1 thing that will break it.** Using the Python SDK avoids it entirely.

### 4.7 Function calling on the Interactions API (different shape)

Verbatim request:

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "gemini-3.8-flash",
    "input": "Schedule a meeting with Bob and Alice for 03/27/2025 at 10:00 AM about Q3 planning.",
    "tools": [{
        "type": "function",
        "name": "schedule_meeting",
        "description": "Schedules a meeting with specified attendees at a given time and date.",
        "parameters": {
          "type": "object",
          "properties": {
            "attendees": {"type": "array", "items": {"type": "string"}},
            "date": {"type": "string"},
            "time": {"type": "string"},
            "topic": {"type": "string"}
          },
          "required": ["attendees", "date", "time", "topic"]
        }
    }]
  }'
```

Note: **flat `tools[]` with `"type": "function"`** — no `functionDeclarations` wrapper.

Modes become `tool_choice` inside `generation_config`. Verbatim:

> Control how the model uses tools using `tool_choice` in `generation_config`:
> - `auto` (Default): Model decides whether to call a function or respond directly.
> - `any`: Model is constrained to always predict a function call.
> - `none`: Model is prohibited from making function calls.
> - `validated`: Model ensures function schema adherence.

```json
"generation_config": {
  "tool_choice": {
    "allowed_tools": {
      "mode": "any",
      "tools": ["get_current_temperature"]
    }
  }
}
```

Response (verbatim, from the migrate page) — status becomes `requires_action`:

```json
{
  "id": "int_001",
  "status": "requires_action",
  "steps": [
    {
      "type": "user_input",
      "status": "done",
      "content": [ { "type": "text", "text": "What's the weather in Boston?" } ]
    },
    {
      "type": "function_call",
      "status": "waiting",
      "id": "fc_1",
      "name": "get_weather",
      "arguments": { "location": "Boston, MA" }
    }
  ]
}
```

Submitting the result (verbatim) — note `arguments` not `args`, `call_id`, `result` as a content array:

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta2/interactions" \
-H "Content-Type: application/json" \
-H "x-goog-api-key: $GEMINI_API_KEY" \
-d '{
    "model": "gemini-3.8-flash",
    "previous_interaction_id": "int_001",
    "input": {
        "type": "function_result",
        "call_id": "fc_1",
        "name": "get_weather",
        "result": [
            { "type": "text", "text": "52°F with rain" }
        ]
    }
}'
```

**Naming difference to watch:** legacy = `functionCall.args`; Interactions = `function_call` step with
`arguments`.

---

## 5. Normal text-generation response shape

Sources: <https://ai.google.dev/api/generate-content> (reference) and
<https://ai.google.dev/gemini-api/docs/generate-content/text-generation>.

### 5.1 `GenerateContentResponse` (verbatim JSON representation)

```json
{
  "candidates": [ { object (Candidate) } ],
  "promptFeedback": { object (PromptFeedback) },
  "usageMetadata": { object (UsageMetadata) },
  "modelVersion": string,
  "responseId": string,
  "modelStatus": { object (ModelStatus) }
}
```

Verbatim description:
> Response from the model supporting multiple candidate responses. Safety ratings and content filtering are
> reported for both prompt in `GenerateContentResponse.prompt_feedback` and for each candidate in `finishReason`
> and in `safetyRatings`. The API: - Returns either all requested candidates or none of them - **Returns no
> candidates at all only if there was something wrong with the prompt (check `promptFeedback`)** - Reports
> feedback on each candidate in `finishReason` and `safetyRatings`.

### 5.2 Real example (verbatim)

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          { "text": "At its core, Artificial Intelligence works by learning from vast amounts of data ..." }
        ],
        "role": "model"
      },
      "finishReason": "STOP",
      "index": 1
    },
  ]
}
```

With usage (verbatim, from the migrate page):

```json
{
  "candidates": [
    {
      "content": {
        "parts": [ { "text": "Why did the chicken cross the road? To get to the other side!" } ],
        "role": "model"
      },
      "finishReason": "STOP",
      "index": 0
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 4,
    ...
  }
}
```

**Text lives at `candidates[0].content.parts[0].text`** — confirmed by the doc's own JS snippet repeated on
every text-generation sample: `const content = data['candidates'][0]['content']['parts'][0]['text'];`

⚠️ But `parts` is an array and with thinking models it can hold thought/signature parts. The function-calling
doc itself warns `# Extract tool call details, it may not be in the first part.` **Iterate parts; prefer the
SDK's `response.text` accessor.**

### 5.3 `Candidate` (verbatim JSON representation)

```json
{
  "content": { object (Content) },
  "finishReason": enum (FinishReason),
  "safetyRatings": [ { object (SafetyRating) } ],
  "citationMetadata": { object (CitationMetadata) },
  "tokenCount": integer,
  "groundingAttributions": [ { object (GroundingAttribution) } ],
  "groundingMetadata": { object (GroundingMetadata) },
  "avgLogprobs": number,
  "logprobsResult": { object (LogprobsResult) },
  "urlContextMetadata": { object (UrlContextMetadata) },
  "index": integer,
  "finishMessage": string
}
```
> `finishReason` — Optional. Output only. The reason why the model stopped generating tokens. **If empty, the
> model has not stopped generating tokens.**
> `finishMessage` — Optional. Output only. Details the reason why the model stopped generating tokens. This is
> populated only when `finishReason` is set.

### 5.4 `FinishReason` enum — complete verbatim list

```
FINISH_REASON_UNSPECIFIED   Default value. This value is unused.
STOP                        Natural stop point of the model or provided stop sequence.
MAX_TOKENS                  The maximum number of tokens as specified in the request was reached.
SAFETY                      The response candidate content was flagged for safety reasons.
RECITATION                  The response candidate content was flagged for recitation reasons.
LANGUAGE                    The response candidate content was flagged for using an unsupported language.
OTHER                       Unknown reason.
BLOCKLIST                   Token generation stopped because the content contains forbidden terms.
PROHIBITED_CONTENT          Token generation stopped for potentially containing prohibited content.
SPII                        Token generation stopped because the content potentially contains Sensitive Personally Identifiable Information (SPII).
MALFORMED_FUNCTION_CALL     The function call generated by the model is invalid.
IMAGE_SAFETY                Token generation stopped because generated images contain safety violations.
IMAGE_PROHIBITED_CONTENT    Image generation stopped because generated images has other prohibited content.
IMAGE_OTHER                 Image generation stopped because of other miscellaneous issue.
NO_IMAGE                    The model was expected to generate an image, but none was generated.
IMAGE_RECITATION            Image generation stopped due to recitation.
UNEXPECTED_TOOL_CALL        Model generated a tool call but no tools were enabled in the request.
TOO_MANY_TOOL_CALLS         Model called too many tools consecutively, thus the system exited execution.
MISSING_THOUGHT_SIGNATURE   Request has at least one thought signature missing.
MALFORMED_RESPONSE          Finished due to malformed response.
ESCALATION                  Request was filtered by an escalation rule.
PUP_LIMITED_DISABLED        Indicates that token generation stopped because the user account is limited or disabled due to Prohibited Use Policy (PUP) violations.
```

For LetterLens, the ones worth special-casing: `STOP` (happy path), `MAX_TOKENS` (truncated JSON → your
`json.loads` will throw; raise `maxOutputTokens` or shrink the schema), `SAFETY` / `PROHIBITED_CONTENT` / `SPII`
(a letter photo containing personal data could plausibly trip `SPII`), `MALFORMED_RESPONSE`,
`MISSING_THOUGHT_SIGNATURE`.

### 5.5 `PromptFeedback` + `BlockReason` (verbatim)

```json
{
  "blockReason": enum (BlockReason),
  "safetyRatings": [ { object (SafetyRating) } ]
}
```
> `blockReason` — Optional. **If set, the prompt was blocked and no candidates are returned. Rephrase the prompt.**

```
BLOCK_REASON_UNSPECIFIED  Default value. This value is unused.
SAFETY                    Prompt was blocked due to safety reasons. Inspect safetyRatings to understand which safety category blocked it.
OTHER                     Prompt was blocked due to unknown reasons.
BLOCKLIST                 Prompt was blocked due to the terms which are included from the terminology blocklist.
PROHIBITED_CONTENT        Prompt was blocked due to prohibited content.
IMAGE_SAFETY              Candidates blocked due to unsafe image generation content.
```

**So a prompt-level block returns HTTP 200 with `candidates` absent and `promptFeedback.blockReason` set.**
Any code doing `response["candidates"][0]` will `KeyError`/`IndexError` on a blocked prompt. Guard it.

### 5.6 `UsageMetadata` — full verbatim field list (for token logging)

```json
{
  "promptTokenCount": integer,
  "cachedContentTokenCount": integer,
  "candidatesTokenCount": integer,
  "toolUsePromptTokenCount": integer,
  "thoughtsTokenCount": integer,
  "totalTokenCount": integer,
  "promptTokensDetails": [ { object (ModalityTokenCount) } ],
  "cacheTokensDetails": [ { object (ModalityTokenCount) } ],
  "candidatesTokensDetails": [ { object (ModalityTokenCount) } ],
  "toolUsePromptTokensDetails": [ { object (ModalityTokenCount) } ],
  "serviceTier": enum (ServiceTier)
}
```

Verbatim descriptions:
> `promptTokenCount` — Number of tokens in the prompt. When `cachedContent` is set, this is still the total
> effective prompt size meaning this includes the number of tokens in the cached content.
> `cachedContentTokenCount` — Number of tokens in the cached part of the prompt (the cached content)
> `candidatesTokenCount` — Total number of tokens across all the generated response candidates.
> `toolUsePromptTokenCount` — Output only. Number of tokens present in tool-use prompt(s).
> `thoughtsTokenCount` — Output only. Number of tokens of thoughts for thinking models.
> `totalTokenCount` — **Total token count for the generation request (prompt + thoughts + response candidates).**
> `promptTokensDetails[]` — Output only. List of modalities that were processed in the request input.
> `serviceTier` — Output only. Service tier of the request.

**Log for LetterLens:** `promptTokenCount`, `candidatesTokenCount`, `thoughtsTokenCount`, `totalTokenCount`,
plus `promptTokensDetails` (gives the image-vs-text token split per modality — exactly what you want to know
when a letter photo costs more than expected), `modelVersion` and `responseId` (for support tickets).

`thoughtsTokenCount` is billed and can dominate: the streaming example in §6 shows
`total_thought_tokens: 245` vs `total_output_tokens: 90` for a trivial prompt.

---

## 6. Streaming

### 6.1 Legacy `:streamGenerateContent?alt=sse` (verbatim)

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:streamGenerateContent?alt=sse" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  --no-buffer \
  -d '{
    "contents": [
      { "parts": [ { "text": "Explain how AI works" } ] }
    ]
  }'
```

(`--no-buffer` is in the doc sample and matters for curl.)

Verbatim on the two endpoints:
> `generateContent` (REST): Receives a request and provides a single response after the model has finished its
> entire generation.
> `streamGenerateContent` (SSE): Receives the exact same request, but the model streams back chunks of the
> response as they are generated.
>
> **Request body structure** — The request body is a JSON object that is identical for both standard and
> streaming modes.
>
> **Response body structure** — The response body is similar for both the streaming and standard modes except
> for the following: **Standard mode:** The response body contains an instance of `GenerateContentResponse`.
> **Streaming mode:** The response body contains a stream of `GenerateContentResponse` instances.

### 6.2 What each `data:` line contains (verbatim example)

> The following is series of streaming responses. Each response contains a `responseId` that ties the full
> response together:

```json
{
  "candidates": [
    {
      "content": { "parts": [ { "text": "The image displays" } ], "role": "model" },
      "index": 0
    }
  ],
  "usageMetadata": { "promptTokenCount": ... },
  "modelVersion": "gemini-3.8-flash",
  "responseId": "mAitaLmkHPPlz7IPvtfUqQ4"
}
...
{
  "candidates": [
    {
      "content": { "parts": [ { "text": " the following materials:\n\n*   **Wood:** The accordion and the violin are primarily" } ], "role": "model" },
      "index": 0
    }
  ],
  "usageMetadata": { "promptTokenCount": ... }
  "modelVersion": "gemini-3.8-flash",
  "responseId": "mAitaLmkHPPlz7IPvtfUqQ4"
}
```

So each SSE `data:` payload is a **full `GenerateContentResponse` object containing a text delta** (not an
accumulated string), all sharing one `responseId`.

### 6.3 How to detect completion — **PARTIALLY CONFIRMED**

The docs do **not** show a terminator line for `:streamGenerateContent?alt=sse`, and they do **not** state
whether a `data: [DONE]` sentinel is emitted. What is documented:
- `finishReason` is "Optional. Output only. … **If empty, the model has not stopped generating tokens.**"
  → the chunk whose candidate carries a non-empty `finishReason` is the last content chunk.
- The intermediate chunks in the sample above have **no** `finishReason`.

**Recommended detection: treat the chunk with a non-empty `candidates[].finishReason` as the end, and also
treat stream close as end.** Do not rely on a `[DONE]` sentinel on the legacy endpoint — **UNCONFIRMED**.
(The *Interactions* endpoint does emit `data: [DONE]`; see below. Do not assume parity.)

### 6.4 Interactions streaming — fully documented, with `[DONE]`

Source: <https://ai.google.dev/gemini-api/docs/streaming> ("Streaming interactions")

Verbatim event stream:

```
data: {"interaction":{"id":"v1_...","status":"in_progress","object":"interaction","model":"gemini-3.8-flash"},"event_type":"interaction.created"}

data: {"interaction_id":"v1_...","status":"in_progress","event_type":"interaction.status_update"}

data: {"index":0,"step":{"type":"thought"},"event_type":"step.start"}

data: {"index":0,"delta":{"signature":"...","type":"thought_signature"},"event_type":"step.delta"}

data: {"index":0,"event_type":"step.stop"}

data: {"index":1,"step":{"type":"model_output"},"event_type":"step.start"}

data: {"index":1,"delta":{"text":"1, 2, 3, 4, 5, 6, ","type":"text"},"event_type":"step.delta"}

data: {"index":1,"delta":{"text":"7, 8, 9, 10, 11, 12, 13,","type":"text"},"event_type":"step.delta"}

data: {"index":1,"event_type":"step.stop"}

data: {"interaction":{"id":"v1_...","status":"completed","usage":{"total_tokens":346,"total_input_tokens":11,"input_tokens_by_modality":[{"modality":"text","tokens":11}],"total_cached_tokens":0,"total_output_tokens":90,"total_tool_use_tokens":0,"total_thought_tokens":245},"created":"2026-05-12T18:44:51Z","updated":"2026-05-12T18:44:51Z","service_tier":"standard","object":"interaction","model":"gemini-3.8-flash"},"event_type":"interaction.completed"}

data: [DONE]
```

Interactions `event_type` values seen: `interaction.created`, `interaction.status_update`, `step.start`,
`step.delta`, `step.stop`, `interaction.completed`, then literal `data: [DONE]`.
Completion detection: **`event_type == "interaction.completed"`**, then `data: [DONE]`.
Usage lands on the `interaction.completed` event under `interaction.usage` with a *different* field vocabulary
than `usageMetadata`: `total_tokens`, `total_input_tokens`, `input_tokens_by_modality[]`,
`total_cached_tokens`, `total_output_tokens`, `total_tool_use_tokens`, `total_thought_tokens`.

Streaming function calls on Interactions emit `step.start` with `step.type == "function_call"` and then
`step.delta` with `delta.type == "arguments"` carrying `delta.partial_arguments` (string fragments of JSON that
you concatenate and `json.loads` at the end). Verbatim from the function-calling page:

```python
elif event.event_type == "step.delta":
    if event.delta.type == "arguments":
        if event.index in current_calls:
            current_calls[event.index]["arguments"] += event.delta.partial_arguments
    elif event.delta.type == "text":
        print(event.delta.text, end="", flush=True)
```

---

## 7. Python SDK

Source: <https://ai.google.dev/gemini-api/docs/libraries> ("Last updated 2026-06-22 UTC") and
<https://pypi.org/pypi/google-genai/json> (fetched 2026-10-03).

### 7.1 Package name — `google-genai`. `google-generativeai` is DEPRECATED.

Verbatim from the libraries page:

> When building with the Gemini API, we recommend using the **Google GenAI SDK**. These are the official,
> production-ready libraries … They are in General Availability and used in all our official documentation and examples.
>
> **Python** — Library: `google-genai` — GitHub Repository: `googleapis/python-genai` — Installation:
> `pip install google-genai`
>
> JavaScript — Library: `@google/genai` — `npm install @google/genai`
> Go — `google.golang.org/genai` — `go get google.golang.org/genai`
> Java — `com.google.genai:google-genai:1.0.0`
> C# — `Google.GenAI` — `dotnet add package Google.GenAI`

Legacy table, verbatim:

> The legacy libraries don't provide access to recent features (such as Live API and Veo) and are
> **deprecated as of November 30th, 2025.**
>
> | Language | Legacy library | Support status | Recommended library |
> | Python | `google-generativeai` | Not actively maintained | `google-genai` |
> | JavaScript/TypeScript | `@google/generativeai` | Not actively maintained | `@google/genai` |
> | Go | `google.golang.org/generative-ai` | Not actively maintained | `google.golang.org/genai` |
> | Dart and Flutter | `google_generative_ai` | Not actively maintained | Use Genkit Dart or Firebase AI Logic |
> | Swift | `generative-ai-swift` | Not actively maintained | Use Firebase AI Logic |
> | Android | `generative-ai-android` | Not actively maintained | Use Firebase AI Logic |

> As of May 2025, the Google GenAI SDK has reached General Availability (GA) across all supported platforms.

### 7.2 Version and Python requirement

From PyPI JSON metadata for `google-genai` (fetched 2026-10-03):
- Latest version: **2.28.0**
- `requires_python`: **`>=3.10`**
- Summary: `GenAI Python SDK`

**So: Python 3.10+.** (The libraries doc page itself does not state a Python version — this comes from PyPI,
which is the package's own authoritative metadata.)

```
pip install google-genai        # >= Python 3.10
```

### 7.3 Import + client construction (verbatim)

```python
from google import genai
from google.genai import types

client = genai.Client()                        # reads GEMINI_API_KEY / GOOGLE_API_KEY
# or
client = genai.Client(api_key="YOUR_API_KEY")
```

Note the import is `from google import genai` — **not** `import google.generativeai as genai` (that is the
deprecated package).

### 7.4 Text generation

```python
from google import genai
client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash-lite", contents="Tell me a joke."
)
print(response.text)
```
(verbatim from the migrate page; swap in `gemini-3.8-flash`.)

Interactions equivalent (verbatim from the streaming page):
```python
stream = client.interactions.create(
    model="gemini-3.8-flash",
    input="Explain quantum computing in simple terms.",
    stream=True,
)
```

### 7.5 Image input
See §2.7 — `types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')`, or `client.files.upload(file=...)`.

### 7.6 Structured output
See §3.9 — `config={"response_format": {"text": {"mime_type": "application/json", "schema": Recipe.model_json_schema()}}}`.
Pydantic models are first-class; verbatim:
> In addition to supporting JSON Schema in the REST API, the Google GenAI SDKs make it easy to define schemas
> using Pydantic (Python) and Zod (JavaScript).

Parse with `Recipe.model_validate_json(response.text)`.

### 7.7 Function calling
```python
tools = types.Tool(function_declarations=[schedule_meeting_function])
# ... and reading the call:
function_call = response.candidates[0].content.parts[0].function_call
print(f"Requested tool: {function_call.name}")
```
Forced mode: see §4.5.

**Automatic function calling is Python-only.** Verbatim:
> When using the Python SDK, you can provide Python functions directly as tools. The SDK converts these
> functions into declarations, manages the function call execution, and handles the response cycle for you.
> Define your function with type hints and a docstring. For optimal results, it is recommended to use
> Google-style docstrings. The SDK will then automatically: Detect function call responses from the model. Call
> the corresponding Python function in your code. Send the function's response back to the model.

### 7.8 Streaming
The legacy streaming Python call name (`generate_content_stream`) was **not captured verbatim** in this task's
fetches — **UNCONFIRMED**. The Interactions form is confirmed: `client.interactions.create(..., stream=True)`
yielding events with `event_type` / `delta` (see §6.4).

### 7.9 SDK retry behaviour (useful, verbatim)

From <https://ai.google.dev/gemini-api/docs/troubleshooting>:
> The official client SDKs for the Gemini API, such as the Python SDK, include **automatic retry logic with
> exponential backoff by default** for handling transient errors like timeouts, network issues, and rate limits
> (429 and 5xx status codes). For example, the Python SDK automatically retries transient errors **up to four
> times with an initial delay of approximately 1 second and a maximum delay of 60 seconds.**

---

## 8. Errors — status codes and JSON body

Source: <https://ai.google.dev/gemini-api/docs/generate-content/api-errors> ("Last updated 2026-09-20 UTC")

### 8.1 Error body format (verbatim)

> When a GenerateContent request fails, the API sets the HTTP status code (such as 400 Bad Request, 403
> Forbidden, or 429 Too Many Requests) and returns a JSON response body containing gRPC status details:

```json
{
  "error": {
    "code": 400,
    "message": "API key not valid. Please pass a valid API key.",
    "status": "INVALID_ARGUMENT",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.ErrorInfo",
        "reason": "API_KEY_INVALID",
        "domain": "googleapis.com",
        "metadata": {
          "service": "generativelanguage.googleapis.com"
        }
      },
      {
        "@type": "type.googleapis.com/google.rpc.LocalizedMessage",
        "locale": "en-US",
        "message": "API key not valid. Please pass a valid API key."
      }
    ]
  }
}
```

Fields (verbatim):
> `code` — integer — The HTTP status code.
> `message` — string — A human-readable description of the error.
> `status` — string — The gRPC status code in SCREAMING_CASE.
> `details` — array — Additional error context, such as `ErrorInfo` or `LocalizedMessage`.

### 8.2 Status-code table (verbatim)

| HTTP | Status | Description | Example | Solution |
|---|---|---|---|---|
| 400 | `INVALID_ARGUMENT` | The request body is malformed. | There is a typo, or a missing required field in your request. | Check the API reference for request format, examples, and supported versions. Using features from a newer API version with an older endpoint can cause errors. |
| 400 | `FAILED_PRECONDITION` | Gemini API free tier is not available in your country. Please enable billing on your project in Google AI Studio. | You are making a request in a region where the free tier is not supported, and you have not enabled billing. | To use the Gemini API, you will need to setup a paid plan using Google AI Studio. |
| 402 | `RESOURCE_EXHAUSTED` | Your Prepay credit balance is depleted. | Your billing account has run out of Prepay credits, so every API key linked to that billing account stops working. | Add credits to your billing account, or turn on auto-reload. **Don't retry this request: it won't succeed until credits are added.** |
| 403 | `PERMISSION_DENIED` | Your API key doesn't have the required permissions. | You are using the wrong API key; you are trying to use a tuned model without going through proper authentication. | Check that your API key is set and has the right access. |
| 404 | `NOT_FOUND` | The requested resource wasn't found. | An image, audio, or video file referenced in your request was not found. | Check if all parameters in your request are valid for your API version. |
| 429 | `RESOURCE_EXHAUSTED` | You've exceeded one of the API's rate limits (RPM, TPM, RPD, spend, etc.). | You are sending too many requests, using too many tokens, or exceeding spend-based limits for your account's billing history and tier. | Verify that you're within the model's rate limits. Wait and retry after a short period. Reduce the rate or size of your requests. Request a rate limit increase if needed. |
| 499 | `CANCELLED` | The operation was cancelled, typically by the caller. | The client closed the connection before the API could finish responding. | Check if your client or network infrastructure is prematurely closing the connection (e.g., due to a client-side timeout). |
| 500 | `INTERNAL` | An unexpected error occurred on Google's side. | Your input context is too long. | Check the status page. Reduce your input context or temporarily switch to another model. |
| 503 | `UNAVAILABLE` | The service may be temporarily overloaded or down. | The service is temporarily running out of capacity. | Check the status page; temporarily switch to another model; wait and retry. |
| 504 | `DEADLINE_EXCEEDED` | The service is unable to finish processing within the deadline. | Your prompt (or context) is too large to be processed in time. | Set a larger 'timeout' in your client request to avoid this error. |

### 8.3 Answers to the spec's four cases

| Case | HTTP | `status` | Confidence |
|---|---|---|---|
| **Bad model ID** | **404 `NOT_FOUND`** | `NOT_FOUND` | **Medium.** The table documents 404 `NOT_FOUND` = "The requested resource wasn't found", but its *example* is a missing media file, not a bad model name. A bad model string in the URL path is a missing resource, so 404 is the expected code. The exact `message`/`reason` for a bad model is **UNCONFIRMED**. |
| **Quota exceeded** | **429 `RESOURCE_EXHAUSTED`** | `RESOURCE_EXHAUSTED` | **High** — verbatim. Note **402 `RESOURCE_EXHAUSTED`** is a *different* case (prepay credits gone) and must **not** be retried. |
| **Bad API key** | **400 `INVALID_ARGUMENT`** with `details[].reason == "API_KEY_INVALID"` | `INVALID_ARGUMENT` | **High** — this is the verbatim example body in §8.1. A *valid-but-unauthorized* key gives **403 `PERMISSION_DENIED`**. So: malformed/invalid key → 400; wrong-permissions key → 403. |
| **Malformed request** | 400 `INVALID_ARGUMENT` | `INVALID_ARGUMENT` | High. |

### 8.4 Retry policy (verbatim, troubleshooting page)

> If you receive an error indicating that you should retry your request (such as a 429 `RESOURCE_EXHAUSTED` or
> 503 `UNAVAILABLE`), we recommend implementing an exponential backoff strategy.
>
> **Retry on specific errors:** Only retry on transient errors (like 429, 408, or 5xx). **Do not retry on client
> errors (like 400, 402, or 403)** as they indicate issues like invalid API keys, depleted Prepay credits, or
> bad syntax.

---

## 9. LetterLens checklist (what to actually build)

Recommended path for a hackathon on the legacy-but-supported `generateContent`:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [{
      "parts": [
        { "inline_data": { "mime_type": "image/jpeg", "data": "<raw base64, no newlines, no data: prefix>" } },
        { "text": "Extract the fields from this letter." }
      ]
    }],
    "generationConfig": {
      "responseFormat": {
        "text": {
          "mimeType": "application/json",
          "schema": {
            "type": "object",
            "properties": {
              "sender":      { "type": "string",  "description": "Who sent the letter." },
              "received_on": { "type": "string",  "format": "date", "description": "Date on the letter." },
              "category":    { "type": "string",  "enum": ["bill", "legal", "medical", "marketing", "other"] },
              "amount_due":  { "type": ["number", "null"], "description": "Amount owed, or null." },
              "actions":     { "type": "array",  "items": { "type": "string" } }
            },
            "required": ["sender", "category", "actions"]
          }
        }
      }
    }
  }'
```

Then read: `candidates[0].content.parts[*].text` (scan parts), `json.loads` it, validate with Pydantic,
log `usageMetadata.*`, and branch on `finishReason` / `promptFeedback.blockReason`.

Hard rules learned here:
1. Downscale images so the **whole request** stays under **20MB** after base64 (≈ 14MB of original bytes), else Files API.
2. Base64 must be unwrapped (`base64 -w0`), raw, no `data:` prefix.
3. Put the text part **after** the image part.
4. Use `responseFormat.text.{mimeType,schema}`, not the deprecated `responseSchema`.
5. Use `{"type": ["string","null"]}`, not `nullable`.
6. Don't send `propertyOrdering` (Gemini 2.0 only); key order in the schema is honoured.
7. Never index `candidates[0]` or `parts[0]` blindly.
8. Don't retry 400/402/403; do retry 429/5xx with backoff.
9. Raise `mediaResolution` if the model misreads small print on a scanned letter.
10. If you hand-roll multi-turn function calling over REST, you must round-trip `thought_signature` or you get
    `MISSING_THOUGHT_SIGNATURE`. The Python SDK handles it.

---

## 10. Source URLs fetched in this task (2026-10-03)

| What | URL | Page "Last updated" |
|---|---|---|
| Image understanding (legacy) | https://ai.google.dev/gemini-api/docs/generate-content/image-understanding | 2026-09-04 |
| Text generation / request+response structure (legacy) | https://ai.google.dev/gemini-api/docs/generate-content/text-generation | 2026-09-17 |
| Structured outputs (legacy) | https://ai.google.dev/gemini-api/docs/generate-content/structured-output | 2026-09-02 |
| Function calling (legacy) | https://ai.google.dev/gemini-api/docs/generate-content/function-calling | — |
| API errors (legacy) | https://ai.google.dev/gemini-api/docs/generate-content/api-errors | 2026-09-20 |
| API key setup | https://ai.google.dev/gemini-api/docs/generate-content/api-key | — |
| Document processing (legacy) | https://ai.google.dev/gemini-api/docs/generate-content/document-processing | — |
| `generateContent` REST reference (GenerationConfig, Candidate, FinishReason, UsageMetadata, Schema, ResponseFormatConfig) | https://ai.google.dev/api/generate-content | — |
| Structured output (Interactions) | https://ai.google.dev/gemini-api/docs/structured-output | — |
| Function calling (Interactions) | https://ai.google.dev/gemini-api/docs/function-calling | — |
| Streaming interactions | https://ai.google.dev/gemini-api/docs/streaming | — |
| Interactions overview | https://ai.google.dev/gemini-api/docs/interactions-overview | — |
| Migrating to the Interactions API | https://ai.google.dev/gemini-api/docs/migrate-to-interactions | — |
| Libraries / SDK packages | https://ai.google.dev/gemini-api/docs/libraries | 2026-06-22 |
| Models list | https://ai.google.dev/gemini-api/docs/models | — |
| Troubleshooting / retries | https://ai.google.dev/gemini-api/docs/troubleshooting | — |
| `google-genai` package metadata | https://pypi.org/pypi/google-genai/json | live, fetched 2026-10-03 |

### Not fetched — open questions for a future pass
- `/gemini-api/docs/generate-content/media-resolution` — exact `mediaResolution` enum values. **UNCONFIRMED.**
- `/gemini-api/docs/interactions-breaking-changes-may-2026` — contents. **UNCONFIRMED.**
- A verbatim doc example combining **image input + structured output** in one request. **Not found.**
- A verbatim REST example of `toolConfig.functionCallingConfig` for the legacy endpoint. **Not found** (§4.5 is a reconstruction).
- Whether legacy `:streamGenerateContent?alt=sse` emits a `data: [DONE]` sentinel. **Not documented.**
- Legacy Python streaming method name (`generate_content_stream`). **Not captured verbatim.**

---

## Independent verification (adversarial pass)

**Verifier:** second agent, 2026-10-03. **Method:** every page below was re-fetched in this task. Where
`WebFetch`'s summarising model gave inconsistent answers (it twice reported that `ai.google.dev/api/generate-content`
contains *no* occurrences of the word "deprecated" — it contains 152), I downloaded the raw HTML with `curl`,
stripped tags, and grepped the text directly. All verbatim strings below come from those stripped-text files.

**Headline:** 26 of 28 claims CONFIRMED verbatim, 1 REFUTED (claim 25 — shut-down models listed as live),
1 CONFIRMED-but-misleading (claim 27 — a verbatim image + JSON-mode REST example *does* exist and the note
says none does). Two additional errors found in the note body (§2 snake_case claim; §1 model list).
Three of the note's own open questions are now closed.

### Verdict table

| # | Verdict | Note |
|---|---|---|
| 1 | **CONFIRMED** | `<title>` of every `/generate-content/*` page ends `… \| Gemini Generate Content API (Legacy) \| Google AI for Developers` — verified on image-understanding, function-calling, structured-output, text-generation, api-errors. Verbatim sentence confirmed byte-for-byte. `/v1beta/interactions` confirmed on interactions-overview (see #28). |
| 2 | **CONFIRMED** | Verbatim curl, endpoint, `x-goog-api-key` header and snake_case `inline_data`/`mime_type`/`data` all match. |
| 3 | **CONFIRMED** | Both sentences verbatim. `file_data{mime_type,file_uri}` confirmed. |
| 4 | **CONFIRMED** | MIME list, "maximum of 3,600 image files per request", 258-token/384px/768x768 all verbatim. |
| 5 | **CONFIRMED** | `-w0` / `--input` / `-b 0` all present; raw base64, no `data:` prefix. |
| 6 | **CONFIRMED** | Raw-text grep confirms `responseSchema (deprecated)` + `This item is deprecated!` + `Deprecated. Use responseFormat instead.`; `responseMimeType` carries no deprecation marker. See addition A1. |
| 7 | **CONFIRMED** | REST/Python/Interactions shapes all verbatim. The note's warning that the doc's own curl has broken brace nesting is **correct** — verified (see A2). |
| 8 | **CONFIRMED** | Subset list verbatim. `nullable` appears **0 times** on the structured-output page, and only inside the (deprecated) `Schema` proto on the reference page. |
| 9 | **CONFIRMED** | Both verbatim sentences confirmed; `propertyOrdering` appears exactly once on the page, in the Gemini-2.0 footnote. |
| 10 | **CONFIRMED** | `tools[].functionDeclarations[]` REST curl verbatim at three places on the page. |
| 11 | **CONFIRMED** | Four modes, verbatim, in the order VALIDATED / AUTO / ANY / NONE, with VALIDATED described as "Default mode for tool combination (when built-in tools or structured outputs also enabled)". |
| 12 | **CONFIRMED** | Grepped every occurrence of `toolConfig` / `functionCallingConfig` on the page: all are Python / JavaScript / Go SDK code. No REST block. The page's only REST curls are the three `functionDeclarations` ones plus a multimodal `functionResponse` one. The note's reconstruction is still a reconstruction. |
| 13 | **CONFIRMED** | `{id,name,args}`, "Include this exact `id` in your `functionResponse`", `contents.push(response.candidates[0].content)` then `{role:'user',parts:[{functionResponse:…}]}`, and the comment "Extract tool call details, it may not be in the first part." — all verbatim. |
| 14 | **CONFIRMED** | "passing back thought signatures is mandatory for function calling" verbatim; `MISSING_THOUGHT_SIGNATURE` = "Request has at least one thought signature missing." verbatim in the reference enum. |
| 15 | **CONFIRMED** | `GenerateContentResponse` JSON representation matches field-for-field; "Returns no candidates at all only if there was something wrong with the prompt (check `promptFeedback`)" verbatim; `blockReason` = "If set, the prompt was blocked and no candidates are returned. Rephrase the prompt." verbatim; BlockReason enum is exactly the six values listed. |
| 16 | **CONFIRMED** | All 22 enum values present, in exactly the claimed order, with the claimed descriptions. "If empty, the model has not stopped generating tokens." verbatim. |
| 17 | **CONFIRMED** | All 11 fields present in exactly that order; `totalTokenCount` = "Total token count for the generation request (prompt + thoughts + response candidates)." verbatim. |
| 18 | **CONFIRMED** | `:streamGenerateContent?alt=sse` + `--no-buffer` verbatim; "The request body is a JSON object that is identical for both standard and streaming modes"; sample chunks carry text **deltas** ("The image displays" then " the following materials:…"), one shared `responseId`, and `modelVersion` + `usageMetadata` on each chunk. |
| 19 | **CONFIRMED** | `DONE` occurs **0 times** on the whole text-generation page. On the Interactions streaming page it occurs 4 times, as `data: [DONE]`. See addition A3. |
| 20 | **CONFIRMED** | `pip install google-genai`; `google-generativeai` → "Not actively maintained"; "deprecated as of November 30th, 2025." verbatim. "GOOGLE_API_KEY takes precedence" verbatim on the api-key page. |
| 21 | **CONFIRMED** | Live PyPI JSON re-fetched: `version` = `2.28.0`, `requires_python` = `>=3.10`, `summary` = `GenAI Python SDK`. |
| 22 | **CONFIRMED** | Error body JSON identical field-for-field including both `details[]` entries; field table ("The gRPC status code in SCREAMING_CASE") verbatim; 400/402/403/404/429 rows verbatim, including "Don't retry this request: it won't succeed until credits are added." |
| 23 | **CONFIRMED** | The 404 row's Example really is "An image, audio, or video file referenced in your request was not found." No bad-model-ID message or `reason` string appears anywhere on the page. The note's "medium" confidence is the right call. |
| 24 | **CONFIRMED** | Both sentences verbatim, including the parenthetical lists `(like 429, 408, or 5xx)` and `(like 400, 402, or 403)`. |
| 25 | **REFUTED** | See below — this is the one claim that will break a build. |
| 26 | **CONFIRMED (with a sourcing correction)** | `"mediaResolution" : enum ( MediaResolution )` is in the GenerationConfig JSON representation — but the reference page's own description is only *"Optional. If specified, the media resolution specified will be used."* The quoted "determines the maximum number of tokens allocated per input image or video frame" is from the **image-understanding** page, about the SDK/proto spelling `media_resolution`. Two pages, not one. **And the enum values are no longer unknown** — see A4. |
| 27 | **CONFIRMED but materially incomplete** | See below. |
| 28 | **CONFIRMED exactly** | Raw grep of the migrate page: `v1beta2/interactions` = **9** occurrences, `v1beta/interactions` = **0**. interactions-overview = `v1beta/interactions` only. The note's count of 9 is right. (A `WebFetch` summary of the same page claimed 14 — ignore it; the raw count is 9.) |

### Claim 25 — REFUTED

Source re-fetched: <https://ai.google.dev/gemini-api/docs/models> ("Last updated 2026-10-01 UTC").

The page has a **"Previous models"** section introduced verbatim with:

> These models are deprecated and will be shut down soon; migrate to newer models to prevent service interruptions.

and inside it, verbatim row labels:

```
Computer Use (Shut down)                   gemini-2.5-computer-use-preview-10-2025
Gemini 2.0 Flash (Shut down)               gemini-2.0-flash
Gemini 2.0 Flash-Lite (Shut down)          gemini-2.0-flash-lite
Gemini 3.1 Flash-Lite Preview (Shut down)  gemini-3.1-flash-lite-preview
Gemini 3 Pro Preview (Shut down)           gemini-3-pro-preview
```

So:

- **`gemini-2.0-flash` is NOT live.** It is deprecated and marked "(Shut down)". Claim 25 lists it as "Also live". **Do not use it as a cheap fallback.** This is the concrete build hazard in this pass: a fallback chain ending in `gemini-2.0-flash` will fail, probably with the 404 whose message nobody has documented (claim 23).
- Same for `gemini-2.0-flash-lite`, `gemini-3-pro-preview`, `gemini-3.1-flash-lite-preview`, `gemini-2.5-computer-use-preview-10-2025` — all five appear in **§1 of this note's own model list** with no shut-down marker. §1 conflates the live table and the deprecated table. **Treat §1 as unreliable; re-read the models page before picking any model other than `gemini-3.8-flash`.**
- Everything else in claim 25 is confirmed live: `gemini-3.8-flash` (and the page banner says "Gemini 3.8 Flash is now available"), `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite`, `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`.
- One live model missing from §1: **`gemini-omni-1.1-flash`**.
- Note the structured-output support table (§3.5) lists `Gemini 3.1 Flash-Lite Preview`, `Gemini 2.0 Flash` and `Gemini 2.0 Flash-Lite` — i.e. **that table is itself partly about shut-down models.** It does not list 3.6/3.7/3.8. Treat it as stale, not as a capability contract.

### Claim 27 — the note says no doc combines image input with structured output. One does.

Source: <https://ai.google.dev/gemini-api/docs/generate-content/image-understanding>, **"Object detection"** section.
This is a verbatim REST sample combining an inline image part with a JSON-mode `generationConfig` in one request —
exactly the LetterLens shape, and it was missed:

```bash
IMG_PATH="/path/to/image.png"
if [[ "$(base64 --version 2>&1)" = *"FreeBSD"* ]]; then
  B64FLAGS="--input"
else
  B64FLAGS="-w0"
fi
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{
    "contents": [{
      "parts":[
        {
          "inline_data": {
            "mime_type":"image/png",
            "data": "'"$(base64 $B64FLAGS $IMG_PATH)"'"
          }
        },
        {"text": "Detect the all of the prominent items in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."}
      ]
    }],
    "generationConfig": {
      "responseMimeType": "application/json"
    }
  }' 2> /dev/null
```

Python form on the same page, verbatim:

```python
config = types.GenerateContentConfig(
  response_mime_type="application/json"
  )
response = client.models.generate_content(model="gemini-3.8-flash",
                                          contents=[image, prompt],
                                          config=config
                                          )
```

JS form on the same page uses `responseMimeType: "application/json"`.

**What this changes for the build:**
- `generationConfig` *is* documented as composing with inline image input. The orthogonality argument in §3.7 is no longer only an inference.
- What is still **not** shown anywhere is image input + `responseFormat.text.schema` (or + `responseSchema`) in one request. The gap is narrower than §3.7 says: it is now only the `schema` half, not the whole idea.
- So the day-1 smoke test is still required, but it is cheap and its risk is low. **Recommended smoke-test ladder:** (1) image + `responseMimeType` only — this one is doc-backed and must work; (2) image + full `responseFormat.text.{mimeType,schema}`. If (2) fails and (1) passes, you have a clean fallback: `responseMimeType: "application/json"` + schema-in-the-prompt + Pydantic validation.
- `document-processing` really does list, verbatim, "Extract information into structured output formats." as a capability — but that page contains **no** `responseFormat` / `responseMimeType` / `response_format` anywhere, so it is marketing copy, not a contract.

### Additional errors found in the note body (not in the claim list)

**E1 — §2's "the raw REST examples consistently use snake_case" is wrong.** The function-calling page's REST curl for a multimodal function result uses **camelCase inside a REST body**, verbatim:

```json
"parts": [
  {
    "inlineData": {
      "displayName": "instrument.jpg",
      "mimeType": "<MIME_TYPE>",
      "data": "<IMAGE_B64>"
    }
  }
]
```

So the docs mix casings *within REST*. Proto JSON accepts both; just don't build a rule on "REST = snake_case". (`inline_data` in the image examples, `inlineData` here, `functionDeclarations`/`toolConfig`/`responseFormat`/`mimeType` camelCase throughout.)

**E2 — §1's model list mixes live and shut-down models.** See claim 25 above.

**E3 — §3.5's structured-output support table is stale.** See claim 25 above.

### Additions the build will need (A1–A6)

**A1 — there is a *second*, non-deprecated `responseJsonSchema` field, and the docs describe it incoherently.** Verbatim from <https://ai.google.dev/api/generate-content>, GenerationConfig:

> `_responseJsonSchema` **(deprecated)** — `value (Value format)` — *This item is deprecated!* Optional. Output schema of the generated response. This is an alternative to `responseSchema` that accepts JSON Schema. … Deprecated. Use `responseFormat` instead.
>
> `responseJsonSchema` — `value (Value format)` — Optional. An internal detail. Use `responseJsonSchema` rather than this field.

That second description is self-referential and clearly a doc bug. **Don't touch either field.** Use `responseFormat`.

For completeness, the deprecated `_responseJsonSchema` entry documents the *widest* supported JSON-Schema keyword set anywhere in these docs — verbatim, it lists `$id`, `$defs`, `$ref`, `$anchor`, `type`, `format`, `title`, `description`, `enum` (for strings and numbers), `items`, `prefixItems`, `minItems`, `maxItems`, `minimum`, `maximum`, `anyOf`, `oneOf` ("interpreted the same as `anyOf`"), `properties`, `additionalProperties`, `required` — several of which (`$ref`, `$defs`, `anyOf`, `oneOf`) the `responseFormat` subset list (§3.4) does **not** mention. If LetterLens needs `$ref`/`anyOf` in a schema, that is **undocumented for `responseFormat`** — test it, don't assume it. Same entry, verbatim: "Cyclic references are unrolled to a limited degree and, as such, may only be used within non-required properties. (Nullable properties are not sufficient.)"

**A2 — the doc's own structured-output curl is genuinely broken, confirmed.** In the live page the `"required": ["name", "quantity"]` line sits *outside* the nested `items` object and a closing brace is misplaced, so the body as printed is invalid JSON. The corrected version in §3.2 of this note is the one to copy.
(The text-generation streaming sample has a separate typo too: a missing comma after the `"usageMetadata"` object in the second chunk. And the function-calling modes paragraph reads "you can set the mode within the. function_calling_config" — a stray period.)

**A3 — the Interactions SSE stream carries named `event:` lines, not just `data:` lines.** The note's §6.4 transcript shows only the `data:` halves. Verbatim from <https://ai.google.dev/gemini-api/docs/streaming>:

```
event: step.stop
data: {"index":1,"event_type":"step.stop"}

event: interaction.completed
data: {"interaction":{...},"event_type":"interaction.completed"}

event: done
data: [DONE]
```

So each event has both an SSE `event:` name and an `event_type` inside the JSON, and the sentinel is preceded by `event: done`. An SSE client that only reads `data:` still works, but don't be surprised by the `event:` lines.

**A4 — the `MediaResolution` enum values ARE documented; §2.6 marked them UNCONFIRMED.** Verbatim from <https://ai.google.dev/api/generate-content>:

```
MediaResolution — Media resolution for the input media.
MEDIA_RESOLUTION_UNSPECIFIED   Media resolution has not been set.
MEDIA_RESOLUTION_LOW           Media resolution set to low (64 tokens).
MEDIA_RESOLUTION_MEDIUM        Media resolution set to medium (256 tokens).
MEDIA_RESOLUTION_HIGH          Media resolution set to high (zoomed reframing with 256 tokens).
```

Use `"generationConfig": {"mediaResolution": "MEDIA_RESOLUTION_HIGH"}` for dense printed text on a photographed letter. Caveat: these are the *per-image token budgets* (64 / 256 / 256+reframing) — they do **not** obviously reconcile with the 258-tokens-per-768x768-tile model on the image-understanding page. Which one governs billing for `gemini-3.8-flash` is **not documented**; measure it from `usageMetadata.promptTokensDetails` on a real request before promising anyone a cost per letter.

**A5 — the legacy Python streaming method name is `generate_content_stream`; §7.8 marked it UNCONFIRMED.** Verbatim from the text-generation page: `response = client.models.generate_content_stream(` (JS: `ai.models.generateContentStream({...})`).

**A6 — `functionResponse` can carry a multimodal `parts[]` payload, and there is a Gemini-3-only "Function calling with Structured output" feature.** Both are on the function-calling page and both are absent from §4. The `functionResponse` REST shape is wider than §4.4 records:

```json
{
  "functionResponse": {
    "name": "get_image",
    "id": "UNIQUE_CALL_ID_HERE",
    "response": { "image_ref": { "$ref": "instrument.jpg" } },
    "parts": [ { "inlineData": { "displayName": "instrument.jpg", "mimeType": "image/jpeg", "data": "<base64>" } } ]
  }
}
```

i.e. a tool can hand an **image** back to the model. And verbatim:

> **Function calling with Structured output** — Note: This feature is available for Gemini 3 series models. For Gemini 3 series models, you can use function calling with structured output. This lets the model predict function calls or outputs that adhere to a specific schema. As a result, you receive consistently formatted responses when the model doesn't generate function calls.

That is the documented pairing behind `VALIDATED` becoming the default (claim 11), and it is Gemini-3-only. If LetterLens is on `gemini-3.8-flash` it qualifies; on `gemini-2.5-*` it does not.

### Blockers: assessment of the researcher's ten

| Researcher's blocker | Verifier |
|---|---|
| Build on `responseFormat`, not deprecated `responseSchema` | **Agreed, confirmed.** Add: avoid `responseJsonSchema`/`_responseJsonSchema` too (A1). |
| `nullable` not in the subset; use `{"type":["string","null"]}` | **Agreed, confirmed.** "The model ignores unsupported properties." is verbatim, so the silent-failure risk is real. |
| `propertyOrdering` unnecessary except Gemini 2.0 | **Agreed, confirmed.** And Gemini 2.0 is itself shut down (claim 25), so it is now simply dead weight. |
| Four modes; VALIDATED is the default when combining | **Agreed, confirmed** — and A6 shows the exact feature that triggers it. |
| Gemini 3 `id` + thought-signature round-tripping | **Agreed, confirmed verbatim.** |
| No doc confirms image + structured output | **Partly wrong — a verbatim image + `responseMimeType` JSON REST example exists** (claim 27 above). Still smoke-test the `schema` half, but the fallback is now known. |
| Legacy SSE completion is undocumented | **Agreed, confirmed** (`DONE` appears 0 times on the text-generation page). |
| 20MB covers the base64-inflated whole request | **Agreed** — "(text prompts, system instructions, and inline bytes) to 20MB" is verbatim, and base64 is ~4/3, so ~14-15MB of original bytes is the real ceiling. Arithmetic, not doc text. |
| Bad model ID error string undocumented | **Agreed, confirmed.** Don't assert on the message. |
| Interactions path disagreement | **Agreed, confirmed exactly** (9 x `v1beta2`, 0 x `v1beta` on the migrate page). |
| *(new blocker)* | **`gemini-2.0-flash` and four other IDs in §1 are shut down.** Pin `gemini-3.8-flash`; do not build a fallback chain from §1 without re-reading the models page. |

### Pages re-fetched in this verification pass (2026-10-03)

| URL | How | Page "Last updated" |
|---|---|---|
| <https://ai.google.dev/api/generate-content> | curl + raw grep | — |
| <https://ai.google.dev/gemini-api/docs/generate-content/image-understanding> | WebFetch + curl | 2026-09-04 |
| <https://ai.google.dev/gemini-api/docs/generate-content/structured-output> | WebFetch + curl | 2026-09-02 |
| <https://ai.google.dev/gemini-api/docs/generate-content/function-calling> | WebFetch + curl | — |
| <https://ai.google.dev/gemini-api/docs/generate-content/text-generation> | curl | — |
| <https://ai.google.dev/gemini-api/docs/generate-content/api-errors> | curl | 2026-09-20 |
| <https://ai.google.dev/gemini-api/docs/generate-content/api-key> | curl | — |
| <https://ai.google.dev/gemini-api/docs/generate-content/document-processing> | curl | — |
| <https://ai.google.dev/gemini-api/docs/troubleshooting> | curl | — |
| <https://ai.google.dev/gemini-api/docs/libraries> | curl | — |
| <https://ai.google.dev/gemini-api/docs/models> | WebFetch + curl | 2026-10-01 |
| <https://ai.google.dev/gemini-api/docs/streaming> | curl | — |
| <https://ai.google.dev/gemini-api/docs/migrate-to-interactions> | WebFetch + curl | — |
| <https://ai.google.dev/gemini-api/docs/interactions-overview> | curl | — |
| <https://pypi.org/pypi/google-genai/json> | curl (live JSON) | fetched 2026-10-03 |

**Still unverified after this pass:** `/gemini-api/docs/interactions-breaking-changes-may-2026` (exists in site nav, not fetched); whether `$ref`/`$defs`/`anyOf` work inside `responseFormat.text.schema`; whether `mediaResolution` or the 768x768 tile model governs billing; the exact error for a bad model ID; and image input + `responseFormat.text.schema` in one request.

**Methodological warning for future agents:** `WebFetch`'s summarising model gave me three wrong answers on these pages — it reported 0 occurrences of "deprecated" on the reference page (actual: 152), 14 occurrences of `v1beta2` on the migrate page (actual: 9), and omitted `gemini-2.0-flash` from the models page. For anything load-bearing — enum lists, deprecation markers, counts — `curl` the page and grep the text yourself.
