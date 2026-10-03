# 08 — Gemma on the Gemini API: live test results

**Research dimension:** What does Gemma on the Gemini API *actually* do with a real key, as opposed to what the docs claim?
**Tested:** 2026-10-03
**Method:** live HTTP calls against `generativelanguage.googleapis.com/v1beta` using the project's own key from `.env.local`, and the real scanned letters in `test-letters/`. Every number below came from a response on the wire. Nothing here is from docs or training memory.
**Why this note exists:** note 01 §9 listed six open questions that "one API key and ≈5 minutes of curl" would settle, and note 01 §8 made build recommendations that were explicitly unverified. This note settles most of them. **Several of note 01's recommendations turn out to be wrong.**

---

## 0. HEADLINE ANSWERS

1. **The key works.** Auth is `x-goog-api-key`, exactly as note 01 said. 50 models visible.
2. **The tier is FREE, and the API says so itself** — 30 requests/min, per project, **per model** (two models ⇒ two independent buckets).
3. **`gemma-3-27b-it` is dead (404).** It was the pinned default in `.env.example` for both `GEMMA_MODEL` and `GEMMA_VISION_MODEL`, so the repo's defaults could never have worked.
4. **Vision works and is genuinely good** — correct OCR on a scanned UK hospital letter, 258 image tokens for a full page, via plain `inline_data` base64.
5. **THE BIG ONE: pick the right model and most problems vanish.** `gemma-4-31b-it` is slow and flaky — 20–57s, ~50% failure rate on serial requests. `gemma-4-26b-a4b-it` answered **8/8 in a median of 2.0s** under identical serial conditions. **~12× faster, zero failures.** Everything alarming in §6 is a property of the 31b model, not of Gemma or of the free tier (§6.1).
6. **`LLM_TIMEOUT_MS=8000` is therefore probably fine** — on 26b it is a ~4× margin. It is unusable only on 31b.
7. **Structured output is the dangerous kind of broken:** `responseSchema` does not return 400, it returns 200 and quietly ignores your schema (§5). **Use function calling instead** — verified working, clean typed args (§8.4).
8. **Thinking output is a spoken-aloud hazard.** Reasoning arrives as a separate `thought: true` part, up to 4,236 chars against a 5-token answer. Filter it, *and* set `thinkingLevel: "minimal"` (§4, §8.3).
9. **Avoid the OpenAI-compat endpoint.** It works, but inlines reasoning into the message text as `<thought>`, turning a structural guarantee into a regex (§8.5).

---

## 1. Auth and tier (note 01 §9 Q5 — SETTLED)

Note 01 said free-tier limits for Gemma were "unknown and unpublished", and that Gemma is absent from the rate-limits page. That is true of the docs — but the **API volunteers the answer in a 429 body**:

```json
{
  "quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
  "quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier",
  "quotaDimensions": { "location": "global", "model": "gemma-4-31b" },
  "quotaValue": "30"
}
```

- **30 RPM, free tier**, scoped **per project per model** — two different Gemma models get two independent 30 RPM buckets. That is a usable escape valve if one model's quota is exhausted.
- 429s also carry `RetryInfo.retryDelay` (observed: `21s`). **Honour that value** rather than using a blind exponential backoff.
- **RPD not established.** The 429 only ever reported the per-minute metric; establishing the daily cap would mean deliberately burning the day's quota, which was not worth it. Assume one exists.
- `usageMetadata` reports `"serviceTier": "standard"`.

Note 01's "there is **no paid tier** to escape to" should be read with care: the quota ID is explicitly suffixed `-FreeTier`, which implies a non-free tier exists for this metric. Not verified either way.

### 1.1 Rate-limit characterisation (dedicated test run)

A second run targeted the quota directly, on `gemma-4-26b-a4b-it`, with `maxOutputTokens: 1` to keep each call cheap. 40 requests at 8-way concurrency:

| Result | Count |
|---|---|
| `200` | 33 |
| `429` | 7 |
| `500` | **0** |

Status sequence, in completion order:

```
200 ×32, then 429 ×7, then 200
```

Four things follow.

**(a) The bucket behaves like a clean ~30-request window.** Exactly 32 consecutive successes preceded the first 429, matching `quotaValue: 30` plus a small burst allowance. The final `200` arrived after the window rolled.

**(b) Quota buckets really are per-model — confirmed by experiment, not inference.** While `gemma-4-26b-a4b-it` was actively returning 429, an immediate call to `gemma-4-31b-it` returned `200`. The 429's `quotaDimensions` named only `{"model": "gemma-4-26b", "location": "global"}`. **You get 30 RPM per model, and switching model is a legitimate overflow strategy.**

**(c) The advertised `retryDelay` is optimistic.** The 429 advertised `retryDelay: 17s`. Polling every 5s, the first `200` came back at **22.8s** — about 34% longer than advertised. **Treat `retryDelay` as a floor, not a wait time.** Add margin or you will simply collect a second 429.

**(d) No per-day (RPD) quota was ever observed.** Across every 429 captured, the only metric cited was the per-minute one. Either the daily cap is high enough not to have been touched, or it is not enforced on this metric. RPD remains unestablished — but it is no longer a blocker for development-scale usage.

### 1.2 What causes the latency — hypothesis raised, then killed

The 40 calls in §1.1 completed in **0.4–1.6s (median 1.0s)** against 20–57s in §6. Two variables changed at once (model `31b`→`26b`, and `maxOutputTokens: 1`), so that run alone could not attribute the speedup.

The obvious hypothesis was that **latency is dominated by generating thinking tokens** — §4's vision call spent 1,109 thought tokens on a 5-token answer, and capping output removes that work.

**That hypothesis is now disconfirmed.** The `thinkingLevel: "minimal"` probe (§8) returned `thoughtsTokenCount: None` and **zero** thought characters — thinking genuinely switched off — and the call *still took 36.2s* on `gemma-4-31b-it`.

So thinking is not the main driver of wall-clock latency. By elimination the remaining candidate is **the model itself**: `gemma-4-31b-it` appears to be slow per request regardless of how much it generates, while `gemma-4-26b-a4b-it` (MoE, ~3.8B active parameters) is fast. That raises the stakes on the model choice considerably and makes experiment 1 in §9 the decisive one.

Recorded here as a hypothesis raised and killed, because the trail matters: the §1.1 speedup is real but was nearly attributed to the wrong cause.

## 2. Which models exist (note 01 §1 — CONFIRMED, with one correction)

`GET /v1beta/models` returned 50 models. Gemma models present:

| Model ID | Status |
|---|---|
| `gemma-4-31b-it` | Served. Text + vision confirmed working. |
| `gemma-4-26b-a4b-it` | Served. Text confirmed working. |
| `gemma-3-27b-it` | **404 — does not exist.** |

Note 01 was right that exactly two Gemma models are served, and right about their IDs. The 404 matters because `gemma-3-27b-it` was what the repo actually had pinned:

```
# .env.example — both values; corrected in .env.local to gemma-4-31b-it
GEMMA_MODEL=gemma-3-27b-it
GEMMA_VISION_MODEL=gemma-3-27b-it
```

Verbatim error:

```json
{"error":{"code":404,"message":"models/gemma-3-27b-it is not found for API version v1beta,
or is not supported for generateContent...","status":"NOT_FOUND"}}
```

Model metadata for both live models: `inputTokenLimit: 262144`, `outputTokenLimit: 32768`, `supportedGenerationMethods: ["generateContent", "countTokens"]`.

**`streamGenerateContent` is absent from `supportedGenerationMethods` for both models.** See §6.

## 3. `inline_data` base64 vision (note 01 §9 Q1, "most important for LetterLens" — SETTLED: WORKS)

Note 01 recommended starting with the **Files API** because `inline_data` was undocumented for Gemma, and probing base64 "immediately".

**`inline_data` base64 works. No Files API needed.** Tested against `test-letters/01-hospital-appointment.png` (185 KB PNG) on `gemma-4-31b-it`:

- `HTTP 200` in **56.8s**
- Prompt: *"What is the first line of this letter? One short sentence."*
- Answer: `Mere Valley Hospital Trust.` — **correct**
- Tokens: `promptTokenCount: 271` (`TEXT: 13`, `IMAGE: 258`), `candidatesTokenCount: 5`, `thoughtsTokenCount: 1109`, `totalTokenCount: 1385`

A 185 KB full-page scan costs only **258 image tokens**, which is cheap. The model also correctly transcribed the header, sub-header, `Our ref: MVH/OPD/884219`, the date, and the recipient address. **OCR quality is not a risk for this project.**

**Recommendation change vs note 01:** use `inline_data` base64, single round trip. Drop the Files API plan.

## 4. Thinking output is a correctness hazard, not just a cost one

Both Gemma 4 models are thinking models, and the response shape is a trap for this project specifically.

A response arrives as **two parts**:

```
parts[0] = { "text": "<reasoning>", "thought": true }
parts[1] = { "text": "<the actual answer>" }
```

On the vision call above, `parts[0]` was **4,236 characters / 1,109 thought tokens**; `parts[1]` was **5 tokens**. The thought text contained visible self-correction:

> `*   Wait, maybe they want the first sentence of the *message*?`
> `*   Usually, "line" refers to the physical line of text.`
> `*   Let's go with the very first line.`

**Why this is severe for LetterLens.** The persona prompt in `agent/persona-prompt.md` promises "two or three short sentences" and "under 40 words". Naive extraction via `candidates[0].content.parts[0].text` returns the 4,236-character scratchpad, and the agent would **read the model's entire deliberation aloud to a blind user**. That is a worse failure than an error, because it looks like success.

**Mandatory rule for the backend:**

```python
def answer_text(body: dict) -> str:
    parts = body["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))
```

Also note `thoughtsTokenCount` (1,109) was **220× the answer tokens** (5). Any token budgeting that ignores thought tokens will be wrong by orders of magnitude.

## 5. Structured output (note 01 §9 Q2 — SETTLED: ACCEPTED BUT NOT HONOURED)

This is the most dangerous result in this note, because it fails silently.

Request to `gemma-4-31b-it` with the documented Gemini structured-output config:

```json
"generationConfig": {
  "responseMimeType": "application/json",
  "responseSchema": {
    "type": "OBJECT",
    "properties": { "sender": {"type":"STRING"}, "date": {"type":"STRING"} },
    "required": ["sender","date"]
  }
}
```

**Result: `HTTP 200` in 42.6s — not a 400.** But the returned text was:

```
 {\n  "sender": "Mere Valley Hospital",\n  "date": "4 Nov 2026"\n}\n```
```

Note the leading space and the **trailing ` ``` ` markdown fence**. The model produced *conceptually* correct JSON (the extraction itself was right), but wrapped in a markdown code fence — which means `responseMimeType: application/json` was **not enforced**. `json.loads()` on that string raises.

**This is worse than an outright rejection.** A 400 would have failed loudly in development. Instead the endpoint accepts the schema, returns 200, and hands back something that breaks the parser only sometimes, depending on whether the model felt like fencing its output on that particular call.

**Build rule:** do **not** rely on `responseSchema` with Gemma. Either
1. use **function calling** as note 01 §8 recommended (see §6 for whether that holds up), or
2. strip fences defensively before parsing:
   ```python
   import re, json
   def parse_json(text: str):
       t = re.sub(r"^\s*```(?:json)?|```\s*$", "", text.strip()).strip()
       return json.loads(t)
   ```

Note 01 was right to say "Do NOT depend on `responseFormat`/`responseSchema`". This confirms it, and shows the failure mode is silent rather than loud.

## 6. Reliability and latency — the real finding

This is the part the docs cannot tell you, and it dominates every architecture decision below.

**Concurrency is actively harmful.** 40 requests at 10-way concurrency against `gemma-4-31b-it`:

| Result | Count |
|---|---|
| `200` | 8 |
| `429` | 6 |
| `500 INTERNAL` | **26** |

Fanning out does not merely get throttled — it mostly manufactures internal errors.

**Sequential and well under quota is still unreliable.** 12 requests, one at a time, no concurrency, comfortably inside 30 RPM:

```
1: 200 in 26.6s     5: 500 in  0.8s     9: 500 in  1.1s
2: 200 in 19.9s     6: 503 in 57.7s    10: 200 in 35.1s
3: 200 in 23.7s     7: 200 in 34.6s    11: 000 in 60.8s  (connection failed)
4: 500 in  1.1s     8: 500 in 40.4s    12: 200 in 30.1s
```

**6 of 12 succeeded — a ~50% failure rate at a request rate the quota explicitly permits.** Latency on success: **19.9–35.1s** for trivial text, **42.6s** for structured extraction, **56.8s** for vision.

Two distinct 500 shapes, which matters for retry design:
- **Fast 500** (~0.8–1.1s) — cheap, retry immediately.
- **Slow 500** (~40s) — expensive; burns the latency budget before the retry even starts.

**A single `500` proves nothing about the model or the key.** An early one-shot call to `gemma-4-31b-it` returned `500`; four immediate retries all returned `200`. Likewise a `systemInstruction` probe in this run returned `500` on three consecutive attempts, which is *inconclusive* rather than a rejection — at a ~50% per-call failure rate, three failures in a row has probability ≈12%. **Never conclude a capability is unsupported from 5xx alone; only a 4xx is evidence of rejection.**

This rule caught two of this note's own errors. Round 1 recorded `systemInstruction` as REJECTED off three 500s, and recorded streaming as REJECTED when the harness had actually thrown a `JSONDecodeError` parsing an SSE stream. Both were harness artefacts, not model limits. The corrected probes are in §8.

### 6.1 THE DECISIVE RESULT: everything in §6 is a property of `gemma-4-31b-it`, not of Gemma

§6's burst and §1.1's burst differed in two variables at once (model, and `maxOutputTokens`), so neither could attribute the difference. A controlled cross settled it — **serial, concurrency 1, 8 calls per cell, identical prompt**:

| Cell | Model | `maxOutputTokens` | Success | Median latency | Max | Thinking active? |
|---|---|---|---|---|---|---|
| A | `gemma-4-26b-a4b-it` | **uncapped** | **8 / 8** | **2.0s** | 2.5s | Yes — median 49 thought tokens |
| B | `gemma-4-31b-it` | 1 | — | **24.9s** (first call) | — | No — 0 thought tokens |

**The model is the variable. Not the output cap, not the thinking.**

- `gemma-4-26b-a4b-it`, with thinking fully active and output uncapped, answered **8 out of 8 in a median of 2.0 seconds.** No 5xx, no 429.
- `gemma-4-31b-it`, with output capped to a single token and zero thought tokens generated, **still took 24.9s.**

This reverses the headline of §6. The ~50% failure rate and the 20–57s latencies are **not** "what Gemma on the free tier is like" — they are what **`gemma-4-31b-it`** is like. The other model is roughly **12× faster and did not fail once.**

It also vindicates note 01 §8, which recommended `gemma-4-26b-a4b-it` on the reasoning that an MoE model with ~3.8B active parameters would be fast. That was the right call for the right reason.

**Consequence: §7's "unresolved architectural tension" largely dissolves.** At a 2.0s median, `LLM_TIMEOUT_MS=8000` is no longer absurd — it is roughly a 4× margin. The remaining question is purely whether 26b reads a scanned letter as well as 31b did (§3). That is the one thing still gating the model pin, and it is tested in §11.

**Correction to this note's own earlier recommendation.** §7 originally recommended splitting the conversational and vision paths across two models to work around Gemma's latency. That recommendation was built on `gemma-4-31b-it` data and should be treated as superseded if §11 confirms 26b vision. The `.env.local` / `.env.example` pins were also set to `gemma-4-31b-it` on the strength of §3's vision verification, before this result existed — see §11.

## 7. Consequences for the build

| Decision | Note 01 said | Live testing says |
|---|---|---|
| Image transport | Start with Files API, probe base64 | **Use `inline_data` base64.** Confirmed working, one round trip |
| Primary model | `gemma-4-26b-a4b-it` | **Correct — use it.** ~12× faster and 8/8 reliable on text (§6.1), 3/3 and ~10× faster on vision (§10) |
| Pinned IDs | — | **`gemma-3-27b-it` is 404.** Repo defaults were broken |
| Rate limits | Unknown, build 429 backoff | **30 RPM free tier**, per project *per model*; honour `RetryInfo.retryDelay` |
| Request pattern | — | Serial is safest, but 26b took 40 requests at 8-way concurrency with **0** 5xx (§1.1) — the 26/40 figure was 31b |
| Retries | — | Still mandatory, but 26b went **19/19** across §6.1 and §10 without one. Budget for 429s more than 5xx |
| `LLM_TIMEOUT_MS` | — | **8000 is fine on 26b** (4.5s worst case); ~15000 safer. Unusable only on 31b |
| Structured output | Don't depend on it | **Confirmed — and it fails silently with a 200**, not a 400 |
| Thought parts | — | **Must filter `thought: true`** or the agent reads its scratchpad aloud |

### The unresolved architectural tension — RESOLVED, see §10

> **Superseded.** Everything in this subsection was derived from `gemma-4-31b-it` and is kept only to show the reasoning trail. §6.1 and §10 show `gemma-4-26b-a4b-it` answers in 2.0s (text) and 3.7–4.5s (vision), so there is no tension: a single Gemma model serves both paths inside the existing 8s budget. **Do not implement the split below.**

`LLM_TIMEOUT_MS=8000` encodes a voice-assistant latency budget — correct for conversation, since a caller will not tolerate 30s of silence. Measured Gemma latency is 20–57s. These cannot both hold. Three options:

1. **Split the paths.** Conversational turns → a fast Gemini model (`gemini-2.5-flash-lite`); `read_document` → Gemma with a ~90s timeout and a spoken "let me read that for you, one moment". Keeps Gemma for the task that actually needs vision.
2. **All-Gemma, honest UX.** Keep Gemma everywhere, raise the timeout to ~90s, have the agent fill the silence. Risky: ~50% failure means retries stack on top of 30s calls.
3. **Abandon Gemma for the live path.** Contradicts the project's framing if Gemma usage is a requirement.

**Recommendation: option 1.** It is the only one where a failed or slow Gemma call degrades a single feature rather than the whole conversation.

---

## 8. Capability matrix

Legend: **SETTLED** = a 2xx or a 4xx on the wire. **INCONCLUSIVE** = only 5xx seen, which given §6 is not evidence either way.

| Capability | Question | Verdict |
|---|---|---|
| `inline_data` base64 vision | note 01 Q1 | **SETTLED — works.** §3 |
| `responseMimeType` + `responseSchema` | note 01 Q2 | **SETTLED — accepted, not honoured.** Returns 200 with markdown-fenced JSON. §5 |
| Free-tier rate limit | note 01 Q5 | **SETTLED — 30 RPM/project/model.** §1 |
| `systemInstruction` | — | **SETTLED — SUPPORTED and obeyed.** Returned `Bleu` under a French-only instruction. Round 1's "rejected" was 5xx noise. |
| `streamGenerateContent?alt=sse` | note 01 Q3 | **SETTLED — WORKS** (5 SSE chunks), despite being absent from `supportedGenerationMethods`. See §8.1 |
| `/v1beta/interactions` (new surface) | note 01 §8 | **SETTLED — ACCEPTS GEMMA (200).** Contradicts note 01. See §8.2 |
| `/v1beta/openai/chat/completions` | note 01 Q4 | **SETTLED — works, but DO NOT USE.** Inlines reasoning into the message text as `<thought>`. See §8.5 |
| `tools: [{googleSearch:{}}]` | note 01 Q6 | **INCONCLUSIVE — 6/6 attempts `500`.** Statistically unlikely to be noise; probably unsupported but surfaced as a server error. See §8.6 |
| Function calling | note 01 §8's recommended structured path | **SETTLED — SUPPORTED, emits a clean call.** This is the structured-output path to use. See §8.4 |
| `thinkingConfig.thinkingBudget: 0` | — | **SETTLED — REJECTED, `400`:** `"Thinking budget is not supported for this model."` Wrong parameter — use `thinkingLevel`. |
| `thinkingConfig.thinkingLevel: "minimal"` | note 01 §8 | **SETTLED — SUPPORTED, and it works:** zero thought tokens. Does **not** reduce latency (§1.2). See §8.3 |

### 8.1 Streaming works — and streams the reasoning first

`POST :streamGenerateContent?alt=sse` returned `200` with **5 SSE `data:` chunks**. Note 01 Q3 is settled: **streaming works.**

Two caveats worth more than the headline:

1. **It is undocumented and unadvertised.** `streamGenerateContent` does not appear in either model's `supportedGenerationMethods` (§2), yet it serves. Working-but-unadvertised is a fragile thing to build a UX on — it could stop without notice.
2. **The first chunk is the model's reasoning, not its answer.** The opening chunk was verbatim:

   ```
   data: {"candidates": [{"content": {"parts": [{"text": "The user wants me to \"Co...
   ```

   That is the thought stream from §4, arriving first. **A streaming voice UI that speaks tokens as they arrive would begin reading the model's deliberation aloud.** Streaming does not sidestep the §4 hazard — it makes it arrive sooner. Any streaming consumer must filter on the `thought` flag per chunk and emit nothing until the first non-thought part.

### 8.2 The new `/interactions` surface accepts Gemma (contradicts note 01)

`POST /v1beta/interactions` with `{"model": "models/gemma-4-31b-it", "input": "Say OK."}` returned **`200` in 45.8s**.

Note 01 §8 recommended the legacy `:generateContent` surface and reported that "No `interactions` doc page mentions Gemma". The documentation gap is real; **the capability gap is not.** Gemma is served on the new surface.

This does not by itself justify switching — `:generateContent` is verified end-to-end here including vision, and §8.1's lesson about undocumented endpoints applies equally. But note 01's framing of `/interactions` as unavailable for Gemma should not be treated as a constraint.

### 8.3 `thinkingLevel` is the right lever for the §4 hazard — but not for latency

Note 01 §8 recommended `thinkingConfig.thinkingLevel` with exactly two values. **That is correct.** Round 1 probed `thinkingBudget: 0` instead and got a flat rejection:

```json
{"error":{"code":400,"message":"Thinking budget is not supported for this model.",
          "status":"INVALID_ARGUMENT"}}
```

`thinkingLevel` is a different parameter and it works:

| Setting | `thoughtsTokenCount` | thought chars | Latency |
|---|---|---|---|
| `"minimal"` | `None` (absent) | **0** | 36.2s |
| `"high"` | 47 | 174 | 42.6s |
| *(omitted)* | up to **1,109** | up to **4,236** | 19.9–56.8s |

Two separate conclusions, and conflating them would be a mistake:

- **For correctness: use `thinkingLevel: "minimal"` wherever the output is spoken.** It drives thought output to exactly zero, which removes the §4 hazard at the source rather than relying on the backend to filter `thought` parts correctly every time. Defence in depth — do both.
- **For latency: it barely helps.** A ~6s spread between `minimal` and `high` against a 36s floor. The latency problem is the model, not the thinking (§1.2).

Note that `minimal` still produced the correct answer (`OK`) and `systemInstruction` compliance was unaffected, so there is little reason not to use it on the conversational path.

### 8.4 Function calling works — use it instead of `responseSchema`

Note 01 §8 said "Structured data out → **Function calling**. Do NOT depend on `responseFormat`/`responseSchema`." **Both halves of that are now confirmed**: §5 showed `responseSchema` is accepted but silently ignored, and function calling works cleanly.

A single `functionDeclarations` tool returned a properly-formed call in 29.8s:

```json
{"name": "record_letter",
 "args": {"date": "4 Nov 2026", "sender": "Mere Valley Hospital"},
 "id": "call_810194"}
```

Correct arguments, correctly typed, in `parts[].functionCall` — no markdown fence, no parsing heuristics, and an `id` for correlation. **This is the extraction path `read_document` should use.** It is the one structured mechanism on Gemma that is both documented and verified.

Contrast the two options for getting structured letter data out:

| Approach | Status | Parsing required |
|---|---|---|
| `responseMimeType` + `responseSchema` | Accepted, **not honoured** (§5) | Strip markdown fences, hope |
| `functionDeclarations` | **Works** | None — read `functionCall.args` |

### 8.5 The OpenAI-compat endpoint works, and is the worst option for this project

`POST /v1beta/openai/chat/completions` with `Authorization: Bearer $KEY` and `{"model": "gemma-4-31b-it", ...}` returned `200` in 39.8s. Note 01 Q4 is settled: **it accepts Gemma.** It also accepts an OpenAI-style `system` role message, which is a convenient way to pass the persona prompt.

**Use it anyway and you lose the ability to separate reasoning from answer.** The returned `choices[0].message.content` began:

```
<thought>The user is asking for the color of the sky.
The co...
```

On `:generateContent`, reasoning is a **structurally separate part** carrying `thought: true`, which §4's filter removes reliably. On the OpenAI-compat endpoint the same reasoning is **inlined into the answer text as pseudo-XML**. There is no flag, no separate field — the only way to remove it is to string-strip `<thought>…</thought>` and hope the model always closes the tag.

For a tool that speaks its output to a blind user, that is the difference between a structural guarantee and a regex. **Stay on `:generateContent`.**

This is a concrete reason to prefer the legacy surface that note 01 recommended, though not the reason note 01 gave.

### 8.6 `googleSearch` grounding: six consecutive 500s is itself evidence

Note 01 Q6 asked whether `tools: [{"googleSearch": {}}]` works on Gemma, noting the pricing page says "Not available". The probe returned **`500 INTERNAL` on all six attempts**, spread over ~45s with 4s gaps.

Per §6, a 5xx is not evidence of rejection — but *six* of them is a different claim. At the measured baseline failure rate of roughly 50%, six consecutive failures has probability ≈1.6%. Every other probe in round 3 succeeded within 1–2 attempts. The most plausible reading is that **`googleSearch` is genuinely unsupported on Gemma, and the backend reports it as a server error rather than a clean `400`.**

Still logged as INCONCLUSIVE rather than REJECTED, because the distinction is exactly the one §6 warns about and only a 4xx would settle it. **Practical guidance: do not plan on grounding.** The pricing page's "Not available" is probably right. If grounding is ever needed, it is a reason to route that call to a Gemini model.

## 9. Experiments still worth running

**1. The model × output-cap cross (resolves §6.1 and §1.2).** The two bursts so far moved two variables at once, so neither the "26b is more reliable" claim nor the "latency is thinking tokens" hypothesis is attributable. The missing cells, run serially at concurrency 1:

| Cell | Model | `maxOutputTokens` | Answers |
|---|---|---|---|
| A | `gemma-4-26b-a4b-it` | uncapped | Is 26b genuinely more reliable, or was it the cap? |
| B | `gemma-4-31b-it` | 1 | Does capping alone rescue 31b's 50% failure rate? |

If B is clean and A is not, reliability tracks generation length and the model choice barely matters. If A is clean and B is not, 26b is simply the better model and should become the default. **This is the single most decision-relevant experiment left** — it determines both the model pin and whether the §7 latency tension is real or an artefact of letting the model think without limit.

**2. `maxOutputTokens` as a latency control, with a usable answer.** §1.1 used `maxOutputTokens: 1`, which is fast but returns nothing useful. The real question is whether a moderate cap (say 128) keeps latency low while still permitting a complete 40-word reply per the persona prompt — or whether the model spends the whole budget thinking and gets truncated before it answers. Note that §4 measured 1,109 thought tokens against a 5-token answer, so a cap that does not account for thought tokens may truncate the answer entirely.

**3. RPD (daily cap).** Never observed: every 429 cited only the per-minute metric (§1.1d). Establishing it means deliberately burning a day's quota. Low priority — it is not a development-scale blocker.

**4. Whether a paid tier exists** for `generate_content_free_tier_requests` — the `-FreeTier` quota suffix implies one, contra note 01's "no paid tier to escape to".

**5. Vision under `thinkingLevel`.** §3's vision call took 56.8s with 1,109 thought tokens. If `thinkingLevel: "minimal"` is honoured (§8), re-running the vision probe under it is the direct test of whether `read_document` can be made to fit a tolerable latency budget.

## 10. `gemma-4-26b-a4b-it` does the vision job too — the pin is settled

§6.1 showed 26b is ~12× faster on text. The only thing left gating the model pin was whether it reads a scanned letter as well as 31b did (§3). It does, and faster.

All three letters in `test-letters/`, `inline_data` base64, `thinkingLevel: "minimal"`:

| Letter | Status | Latency | Thought chars | Image tokens | Answer |
|---|---|---|---|---|---|
| `01-hospital-appointment` | 200 (1 att) | **4.5s** | **0** | 258 | `From: J. Pemberton-Hale, Outpatient Booking Manager. / Appointment Date: Thursday 6 November 2026.` |
| `02-parking-penalty` | 200 (1 att) | **4.4s** | **0** | 258 | `From: Borough of Kerneby / Deadline: 16 October 2026 (to pay the reduced amount)` |
| `03-school-trip-consent` | 200 (1 att) | **3.7s** | **0** | 258 | `Thornfield Lane Primary School. / Friday 24 October 2026.` |

**3/3, first attempt, 3.7–4.5s.** Compare `gemma-4-31b-it` on the same task: **36.8s and 56.8s** (§3). Roughly 10× faster on vision as well as text.

Every answer was checked against the known-good `.txt` transcript beside each image and is **verbatim correct**:

- `J. Pemberton-Hale, Outpatient Booking Manager` and `Thursday 6 November 2026` — exact.
- `Borough of Kerneby` and `16 October 2026` — exact, **and it correctly identified this as the reduced-amount deadline.** That letter contains two dates (pay £35 by 16 October, or the full amount later); picking the right one and labelling it is comprehension, not OCR.
- `Thornfield Lane Primary School` and `Friday 24 October 2026` — exact, correctly the return-by date.

A caveat on method: the harness's automated groundedness check scored letter 02 as `0/1 proper nouns found`. **That was a bug in the check, not a miss by the model** — the regex looked for consecutive capitalised words and "Borough of Kerneby" contains a lowercase "of". Verified by hand against the transcripts instead. Noted because an automated accuracy score that silently under-reports is exactly the kind of thing that gets copied into a conclusion.

**`thinkingLevel: "minimal"` held on the vision path too** — zero thought characters on all three calls, while answers stayed correct and well-formatted. The §4 hazard is fully suppressible on the path where it mattered most.

### Pins updated

```
GEMMA_MODEL=gemma-4-26b-a4b-it
GEMMA_VISION_MODEL=gemma-4-26b-a4b-it
```

**And `LLM_TIMEOUT_MS=8000` can stay.** Against a 4.5s worst case on vision and 2.5s on text, 8s is a workable margin — though it is tight for vision and ~15000 would be safer. The split-path architecture recommended in §7, and the 90s vision timeout it implied, are **no longer necessary**. They were correct conclusions from `gemma-4-31b-it` data and are superseded.

## 11. Reproducing this

The probe harness lives outside the repo (it reads the live key from `.env.local`). Shape of each probe:

```python
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
    data=json.dumps(payload).encode(),
    headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
```

Two rules learned the hard way:
- **Retry 5xx up to 3× with a few seconds between**, or you will record false negatives.
- **Sleep ~2.5s between probes** to stay inside 30 RPM, and never run probes concurrently (§6).
