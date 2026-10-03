# LetterLens — Hackathon Submission Pack

**Event:** Hacktoberfest Hack Day Bradford x Applied AI Society (Bradford Agentic AI Hackathon 2026)
**Submit at:** `mlh.com/events/hacktoberfest-hack-day-bradford-x-applied-ai-society/submissions/new`
**Repo:** https://github.com/llygrace034/vision-impairment-assistance
**License:** Apache License 2.0 (`LICENSE` at repo root)

This file contains four things:

- **[Section A](#section-a--the-writeup)** — the writeup, in headings that paste cleanly into an MLH or Devpost form.
- **[Section B](#section-b--the-90-second-demo-script)** — the demo script (plus a 30-second cut and a one-liner). **A live vision read measures 3.7–4.5 s on the pinned `gemma-4-26b-a4b-it` (note 08 §10, 3/3 on the first attempt), so the 90-second target fits a live read with room to spare.** Read the timing box anyway: it records why we once budgeted two minutes.
- **[Section C](#section-c--prize-track-arguments)** — one paragraph per prize track, including the **track-eligibility issue that has now been fixed** and the one thing still left to verify.
- **[Section D](#section-d--submission-checklist)** — the pre-submit checklist.

Everything marked `<!-- TODO(human): ... -->` is a number or a fact only you can confirm. Search the file for `TODO(human)` before you submit.

---

# Section A — The writeup

## Inspiration

A letter from the hospital arrives on a Tuesday. It is one sheet of A4. It says you have a dermatology appointment at 10:40 on Thursday 6 November, that you should arrive fifteen minutes early, and — in the paragraph nobody reads aloud — that **if you miss two appointments without telling them, you may be referred back to your GP.** If you are blind or have low vision, you do not know any of that. You know an envelope arrived. You find out what it says when someone sighted next comes round, which might be Saturday.

Everything else in that person's life has gone digital and screen-reader-accessible. Banking, email, the GP app, the council. Paper post is the last stubbornly analogue thing left, and it is exactly the channel the NHS, the DVLA, councils and schools still use for the things with deadlines attached. The existing options are bad: wait days for help, or hand your medical correspondence to a stranger. Commercial OCR apps read a letter out — all of it, including the letterhead, the reference number and the parking advice — which is transcription, not understanding, and it does not help you act.

LetterLens is the version we wanted to exist: you hold the letter up and *talk to it*.

## What it does

LetterLens is a voice-first assistant for physical post. You hold a paper letter up to a laptop webcam and have a conversation with it.

1. **You talk, it listens.** The agent opens with "Hi, I'm LetterLens. Hold a letter up to the camera and I'll tell you what it says." No buttons, no menus, no screen required.
2. **It looks before it speaks.** When you show it a letter, the agent calls `read_document`, which captures the current camera frame and runs a Gemma vision pass over it, returning a structured letter object — sender, document type, key dates, amounts, deadline, actions required. The agent is forbidden by its system prompt from saying anything about a letter it has not read.
3. **It explains in plain English.** Two or three short sentences, under forty words: who it's from, what they want, and the date or deadline. Not a transcription. *"This is from Mere Valley Hospital Trust. You have a dermatology appointment on Thursday the sixth of November at 10:40, and they'd like you there fifteen minutes early."*
4. **It offers exactly one next action.** Add it to a calendar (`add_event` → a calendar card and an `.ics` download), set a reminder (`set_reminder`), or draft a reply (`draft_reply`). One, not a menu of three.
5. **It never sends anything.** `draft_reply` writes text you can copy. `add_event` produces a file you download. Nothing leaves the machine on your behalf. That rule is in the system prompt, not just in our heads — you do not want an agent autonomously replying to the council about a parking fine.

It is built and tested against three synthetic letters that cover the realistic spread of official post: an **NHS outpatient appointment** (a date you must attend), a **penalty charge notice** (two money amounts and two different deadlines, where the cheap one expires first), and a **school residential trip consent form** (a deposit, a balance, a form to sign, a medical declaration). Each one ships with a hand-written `--- expected extraction ---` block, so "did the vision pass get it right" is a fixture comparison, not a vibe.

## How we built it

Four moving parts, and — after we measured the API instead of trusting it — still *one* latency budget, because the measurement changed the model rather than the budget.

**The voice layer is an ElevenLabs conversational agent.** The browser holds a WebRTC session to it via the ElevenLabs React SDK (`ConversationProvider` / `useConversation`). ElevenLabs owns turn-taking, VAD, barge-in and speech synthesis; we do not run an audio pipeline. Barge-in is the part we care most about and it is half-automatic: the SDK flushes queued output audio and flips to listening the instant an `interruption` event arrives, and a stale-audio guard drops any chunk whose `event_id` predates the interruption, so the agent physically cannot resume a sentence you cut off (verified in research note `docs/research/04-elevenlabs-react-sdk.md`, §7.1, read out of `client@1.26.0`). The server half is a config switch — `interruption` must be an enabled client event on the agent, or the server never sends the event and the agent talks over you regardless of what the browser does. That one checkbox is the difference between a demo that feels alive and one that feels like an IVR.

**The agent's tools split across two execution surfaces.** This is the architecture, and it is deliberate:

| Tool | Kind | Executes | Why there |
| --- | --- | --- | --- |
| `read_document` | server | Python backend, over webhook | Needs the Gemini API key. Never ships to a browser. |
| `draft_reply` | server | Python backend, over webhook | Must be grounded in the *last* `read_document` result, which is server-side state. |
| `add_event` | client | the browser | Generating and downloading an `.ics` is a browser job. No round trip. |
| `set_reminder` | client | the browser | Same — it renders a card, instantly. |
| `end_call` | system | ElevenLabs | Platform-native. |
| `skip_turn` | system | ElevenLabs | Lets the agent stay deliberately silent while you're still reading or thinking. |

`skip_turn` is small and matters a lot: an assistant for blind users that fills every silence is exhausting. The agent is allowed to say nothing.

**Server tools reach the backend over a public tunnel with a shared-secret header.** `PUBLIC_BASE_URL` (ngrok/cloudflared) points ElevenLabs at the local FastAPI service; `TOOL_WEBHOOK_SECRET` is sent back as a secret request header and checked on every call. We went looking for HMAC request signing on server-tool calls and it does not exist — ElevenLabs documents `ElevenLabs-Signature` HMAC for *post-call* and platform webhooks, not for mid-conversation tool calls (`docs/research/03-elevenlabs-server-tools-and-variables.md`, §6.1). A shared-secret custom header is the documented mechanism, so that's what we built, and we wrote the finding down rather than assuming a signature we'd never have verified.

**The vision pass is Gemma on the Gemini API.** `read_document` takes the captured frame and asks a Gemma multimodal model for a strict letter object: `doc_type`, `sender`, `key_dates`, `deadline`, `amounts`, `actions_required`, plus a confidence signal. Gemma 4 is multimodal (text + image, ~550M-parameter vision encoder, variable aspect ratio and resolution, 256K context) and Google's own Gemma docs demonstrate multilingual OCR explicitly (`docs/research/01-gemma-on-gemini-api.md`, §3 and §4.1) — and we then went and *proved* it on the wire rather than taking the docs' word for it. `docs/research/08-gemma-live-api-test-results.md` §10 records live calls against the pinned `gemma-4-26b-a4b-it` on all three letters in `test-letters/`: HTTP 200 on the first attempt every time, **3.7–4.5 s**, and sender and date verbatim-correct against each known-good `.txt` — including picking the reduced-amount deadline out of the two dates on the parking penalty, which is comprehension rather than OCR — at a cost of **258 image tokens for a full A4 page**. The frame goes up as `inline_data` base64 in a single round trip — note 01 had recommended starting with the Files API, and the live test showed base64 simply works, so we dropped the extra hop. **Neither OCR quality nor latency is a risk on this project, once the model is the right one.** Model IDs are pinned in env (`GEMMA_MODEL`, `GEMMA_VISION_MODEL`) and never hard-coded in source, so swapping the vision model is a config change — which is exactly how we recovered when testing showed the originally pinned ID was dead. See [Section C](#1-best-use-of-gemma-4-google).

**One clock, because the measurement moved the model instead of the budget.** The original design ran everything against one 8-second budget, and the first round of live testing looked like it had killed that: 20–57 seconds, with a ~50 % failure rate on strictly serial requests well inside the free tier's 30 RPM. A controlled head-to-head (note 08, §6.1) showed those numbers belonged to **`gemma-4-31b-it`**, not to Gemma and not to the free tier. On `gemma-4-26b-a4b-it` the same serial test answered **8/8 at a 2.0 s median**, and §10 read all three test letters in **3.7–4.5 s**, 3/3 first attempt. So there is one model and one budget:

| Path | Model | Timeout | Why |
| --- | --- | --- | --- |
| Conversational turns | `gemma-4-26b-a4b-it` (`GEMMA_MODEL`) | `LLM_TIMEOUT_MS=8000` | 2.0 s median, 8/8 (note 08 §6.1) — roughly a 4× margin. The budget sits deliberately inside the ElevenLabs webhook timeout (default 20s, min 5s) so the backend always fails first and returns a speakable string. |
| `read_document` | `gemma-4-26b-a4b-it` (`GEMMA_VISION_MODEL`) | `LLM_TIMEOUT_MS=8000` | 3.7–4.5 s on all three letters with `thinkingLevel: "minimal"` (note 08 §10). Tight but workable; ~15000 would be safer. |

The payoff is simplicity: one Gemma model, one budget, and a 4× latency margin measured rather than assumed (note 08, §§6.1 and 10). The failure mode we kept designing for is still real — `read_document` is the only path to the letter's contents, so a failed read degrades **one feature** and the agent can still talk to you, apologise, and ask you to hold the letter again. And the quota finding survives the simplification: the free tier is 30 RPM scoped per project *per model*, confirmed by experiment (note 08, §1.1b), so if 26b's bucket is exhausted, switching model is a legitimate overflow strategy.

**Stack:** React 19 + Vite + TypeScript (frontend) · FastAPI + httpx + Pydantic (backend) · ElevenLabs Agents (voice, turn-taking, tools) · Gemma via the Gemini API (vision + extraction) · Apache-2.0.

## Challenges we ran into

**Stopping the agent from speaking before it has looked.** A conversational LLM shown a camera feed will happily narrate what it thinks a letter probably says. That is the single worst failure mode in this product — a confidently wrong appointment date is strictly worse than no answer. The fix is a hard operating rule in the system prompt ("call `read_document` before saying anything about it") plus a design rule that low confidence is not a summary: if the vision pass comes back unsure, the agent asks you to flatten the page or hold it closer. It does not guess, and it does not round "probably November" up to a date.

**Structured output is accepted, and then silently ignored.** We need a strict schema out of the vision call. Nobody documents whether that works with image input — we could not find a single Google doc page combining an image part with `responseFormat` in one request (`docs/research/07-gemini-vision-and-structured-output.md`, §3.7), and for Gemma specifically structured output is documented neither as supported nor unsupported (note 01, §4.3). So we tested it. The answer is the worst available one: **sending `responseMimeType: "application/json"` plus a `responseSchema` to `gemma-4-31b-it` returns HTTP 200, not 400 — and the body comes back as markdown-fenced JSON** with a leading space and a trailing ` ``` ` (note 08, §5). The extraction itself was correct; `json.loads()` on it raises. A 400 would have failed loudly on the first run; instead the endpoint nods, ignores the schema, and hands back something that breaks the parser only on the calls where the model felt like fencing its output. So the posture is: **strip fences and parse defensively, then validate the shape server-side in Pydantic regardless.** Note 01's recommended alternative — function calling — is now **verified working** (note 08 §8.4: one `functionDeclarations` tool came back as a clean, correctly typed `functionCall.args` with an `id` and no fence), so it is the fix we intend to land in place of fence-stripping rather than a hope. One honest caveat: §8.4 declared the tool and let the model choose it. *Forcing* the call via `tool_config.function_calling_config` is untested on Gemma, so the backend still has to handle a text-only response.

**The latency budget nearly became an architecture, and the real fix was one line of config.** The design assumed a sub-8-second vision call. Then we pointed real HTTP at a real key and the assumption died: **every single successful call on the model we had just pinned exceeded 8 seconds.** Twelve strictly serial requests, no concurrency, comfortably inside the 30 RPM free-tier quota, produced **six successes and six failures** — latencies of 19.9s, 23.7s, 26.6s, 30.1s, 34.6s and 35.1s for *trivial text*, 42.6s for structured extraction, and **56.8s for the vision call on our own test letter** (note 08, §6). Fanning out made it worse rather than faster: 40 requests at 10-way concurrency against that same model returned **26 `500 INTERNAL`s**. We thought the cause was visible in the token counts — that 56.8s call spent **1,109 thought tokens to produce a 5-token answer** — and concluded wall-clock was dominated by reasoning we never see. **That hypothesis was wrong too, and note 08 §1.2 killed it:** a `thinkingLevel: "minimal"` probe with thinking genuinely off and *zero* thought characters still took **36.2s**.

That looked like a constraint you design to rather than a number you tune. It was neither: it was the wrong model. A controlled serial cross (note 08, §6.1) put `gemma-4-26b-a4b-it` at **8/8 in a 2.0 s median** against 31b's 24.9 s on a single capped token, and §10 then read all three test letters on 26b in **3.7–4.5 s**, 3/3 first attempt, verbatim-correct. So `LLM_TIMEOUT_MS=8000` stayed exactly where it was, both pins became `gemma-4-26b-a4b-it`, and the split-path architecture we had designed was retired before a line of it was written. The spoken *"let me read that for you, one moment"* stays, because four seconds of unexplained silence still tells a blind user nothing. The levers that remain are the honest ones: `pre_tool_speech: "force"` so there is always speech over the pause, `tool_call_sound` so it has an audible floor, serial requests as the safe default — the 26/40 `500 INTERNAL`s above were 31b, and 26b took 40 requests at 8-way concurrency with **zero** 5xx (§1.1), so on the pinned model the thing to budget for is a 429, not a 500 — and honouring the `RetryInfo.retryDelay` the API hands back in a 429 (one advertised 17s and the real recovery took 22.8s, ~34% longer, §1.1c — **treat the advertised delay as a floor, not a wait time**) instead of guessing at a backoff curve. The thing we are proudest of here is that we found this on a Thursday with curl rather than on stage with an audience.
<!-- TODO(human): once the backend exists, log end-to-end wall-clock for read_document (frame capture → spoken first word) across ~10 runs and put real p50/p95 here. Note 08 §10's 3.7–4.5s is the raw model call only; it excludes frame upload, your own retry, and ElevenLabs TTS. Do NOT ship this paragraph with an invented figure. -->

**The model will happily read its own notes out loud.** Both Gemma 4 models are thinking models, and the response comes back as two parts: `parts[0]` is the reasoning, flagged `"thought": true`, and `parts[1]` is the answer. On our vision call `parts[0]` was **4,236 characters** of visible self-correction (*"Wait, maybe they want the first sentence of the message?"*) and `parts[1]` was five tokens. The obvious extraction — `candidates[0].content.parts[0].text` — therefore returns the scratchpad, and a voice agent for blind users would **read the model's entire deliberation aloud** to someone who cannot see that it is deliberation. That is worse than an error, because it looks like success. Filtering on the `thought` flag is a mandatory rule in the backend, not a nicety (note 08, §4) — and streaming does not save you, it just delivers the scratchpad sooner (§8.1).

**Tool errors are hidden from the agent by default.** `tool_error_handling_mode` defaults to `auto`, which for a custom webhook tool means **hide** — the agent is told nothing and will cheerfully hallucinate success (note 03, §7.3). We set it to `summarized` so the agent can say "I couldn't read that, let me try again" instead of inventing an appointment.

**Finding out what the API actually serves.** We wrote seven verified research notes before writing application code, each one quoting primary docs with the fetch date attached. That turned out to matter: the headline finding is that the Gemini API serves exactly **two** Gemma model IDs — `gemma-4-31b-it` and `gemma-4-26b-a4b-it` — and the one we had pinned in `.env.example`, `gemma-3-27b-it`, is neither. Then we wrote an eighth note by doing the thing documentation cannot do for you: live HTTP against a real key. `gemma-3-27b-it` returns a flat **404 — "not found for API version v1beta"**. The repo's defaults could never have worked, at all, on any request. Both pins are now `gemma-4-26b-a4b-it` — the model note 08 §10 verified vision on across all three test letters, at 3.7–4.5 s and 3/3 first attempt.

## Accomplishments that we're proud of

- **The read-before-you-speak rule, enforced architecturally.** The agent has no path to the letter's contents except the vision tool. It cannot bluff, because it has nothing to bluff with.
- **Honest server/client tool separation.** The API key never leaves the backend; the `.ics` never makes a round trip. That split falls out of the privacy and latency requirements, not out of tidiness.
- **Three test letters with hand-written expected extractions.** `test-letters/*.txt` each carry an `--- expected extraction ---` block. Extraction accuracy is a diff against a fixture, not an opinion.
- **Eight research notes that each name their sources and their confidence level.** Several of them say "UNCONFIRMED" out loud. That discipline caught the model-ID problem before it cost us the demo.
- **And then an eighth note that went and proved the other seven wrong where they were wrong.** `docs/research/08-gemma-live-api-test-results.md` is live HTTP against a real key — every number in it came off the wire, and it overturns two of note 01's build recommendations (the Files API and, twice over, the chosen model) while confirming the 8-second latency budget it looked at first like it had killed. The rule it established is worth more than any single finding: *a 5xx is never evidence that a capability is unsupported, only a 4xx is.* Applying that rule caught two false negatives in the note's own first draft.
- **An Agent Skill, not just an app.** `skills/letter-reader/SKILL.md` packages the letter-reading behaviour against the Agent Skill Open Standard, so the extraction logic is portable to any skill-aware agent rather than welded to our frontend.

## What we learned

- **The docs for a model family and the docs for the API that serves it can disagree, and the API wins.** Gemma appears on the Gemma microsite and has **zero** occurrences on the Gemini API models page. If you only read the generic Gemini docs, you will never discover which Gemma IDs are real.
- **Barge-in is a config checkbox, not a feature you build.** The entire client half is already in the SDK. The thing that breaks it is a client event you forgot to enable on the agent. We found this in a doc page, not at 3am during a demo, which is the whole argument for doing the reading first.
- **"The model will probably support that" is a design assumption with a bill attached.** Three capabilities we needed — structured output on Gemma, streaming on Gemma, inline base64 image transport for Gemma — were undocumented rather than unsupported. Each got a planned fallback instead of a prayer, and then five minutes of curl settled all three: base64 vision **works**, streaming **works** (undocumented and absent from `supportedGenerationMethods`, but it serves), and structured output is the bad kind of broken — accepted, 200, schema quietly ignored.
- **The silent failure is the one that costs you.** A 400 is a gift. The three things that nearly sank this build all returned success: `responseSchema` ignored behind a 200, tool errors hidden from the agent behind `tool_error_handling_mode: "auto"`, and a reasoning scratchpad arriving as `parts[0]` of a perfectly valid response. Each would have surfaced on stage as the agent confidently saying something wrong.
- **Change one variable at a time, or you will blame the wrong thing.** We wrote an 8-second timeout into `.env.example` on the strength of a voice-UX rule of thumb, measured 20–57 seconds with a ~50 % failure rate, and nearly rebuilt the architecture around it. Two of our own bursts had moved model *and* `maxOutputTokens` together; a serial cross holding everything else fixed (note 08, §6.1) showed the model was the whole variable — `gemma-4-26b-a4b-it` answered **8/8 at a 2.0 s median** and read all three letters in **3.7–4.5 s** (§10). The rule of thumb was right, the number was right, and the pin was wrong.
- **Accessible defaults are mostly subtraction.** Under 40 words. One action, never three. A tool whose only job is to stay quiet.

## What's next

- **Multi-page letters.** Hold up page two and have the agent merge it into the same letter object.
- **A phone number.** The same ElevenLabs agent over a phone call with an MMS'd photo, for people who do not have a laptop with a webcam.
- **Returning-sender memory.** "This is the third letter from this hospital this month; the last one was an appointment you added to your calendar." (See the Openloft assessment in Section C — this is the feature that would make that track honest.)
- **Keep the fast path fast.** The slow path is gone: `thinkingLevel: "minimal"` is tested and honoured (note 08 §§8.3, 10 — zero thought characters on all three vision calls, answers still correct), and `read_document` already fits inside a conversational turn at 3.7–4.5 s. What is left is hardening: function calling for structured extraction is verified working (§8.4) and should replace fence-stripping — though *forcing* it via `tool_config` is untested, so keep a text-response fallback — and a moderate `maxOutputTokens` cap still needs characterising (§9.2) so a long reply cannot be truncated.
- **Real-document safety work.** The Gemma free tier's terms mean prompts are used to improve Google's products (note 01, §8). Before anyone puts a *real* medical letter in front of this, that needs to be either disclosed in-product or engineered around.
- **A proper accessibility pass.** The UI is currently designed for a sighted presenter at a demo table. It needs a keyboard-only and screen-reader audit against the people it is actually for.

## Try it / Run it

**Prerequisites:** Python 3.11+, Node 20+, a Google AI Studio API key, an ElevenLabs API key and agent ID, and `ngrok` or `cloudflared`.

```bash
git clone https://github.com/llygrace034/vision-impairment-assistance
cd vision-impairment-assistance
cp .env.example .env.local        # then fill it in — .env.local is gitignored

# 1. Backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
<!-- TODO(human): exact backend start command once backend/ has an entrypoint, e.g.
     uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload -->

# 2. Public tunnel (ElevenLabs server tools must be able to reach the backend)
cloudflared tunnel --url http://127.0.0.1:8000
# paste the https URL into PUBLIC_BASE_URL in .env.local, no trailing slash

# 3. Frontend
cd frontend && npm install && npm run dev     # http://localhost:5173
```

Then open `http://localhost:5173`, allow microphone and camera, and hold up `test-letters/01-hospital-appointment.png` (print it, or display it on a second screen).

**Config that must line up or nothing works:**

| Variable | What breaks if it's wrong |
| --- | --- |
| `GEMINI_API_KEY` | `read_document` 401s; the agent says it can't read anything |
| `GEMMA_MODEL` / `GEMMA_VISION_MODEL` | **404 on an unserved model ID.** Both are now `gemma-4-26b-a4b-it`; `gemma-3-27b-it` is dead, and `gemma-4-31b-it` is served but rejected on latency (note 08 §§6.1, 10). See [Section C](#1-best-use-of-gemma-4-google). |
| `CHAT_MODEL` / `VISION_TIMEOUT_MS` | **nothing — both are retired.** They were staged for a split model path that note 08 §10 made unnecessary once 26b measured 2.0 s on text and 3.7–4.5 s on vision. Leave them commented out. |
| `LLM_TIMEOUT_MS` (8000) | one budget for every model call. At 2.0 s median on text and 3.7–4.5 s worst case on vision (note 08 §§6.1, 10) this is roughly a 4× margin — tight for vision, and ~15000 would be safer. Raise it past the webhook timeout and a stalled turn hangs; lower it and healthy reads fail. |
| `ELEVENLABS_AGENT_ID` | the voice session never connects |
| `PUBLIC_BASE_URL` | server tools time out; the agent goes silent after you show the letter |
| `TOOL_WEBHOOK_SECRET` | backend rejects every tool call as unauthenticated |
| `CORS_ORIGINS` | frontend can't reach the backend from the browser |

**Also required on the ElevenLabs agent itself** (not in `.env`):

- `interruption` enabled under **Client Events** — without it, **barge-in does not work and the demo's best moment dies**.
- `tool_error_handling_mode: "summarized"` on `read_document`, so failures are speakable.
- `pre_tool_speech: "force"` on `read_document`, so the vision pause is always covered by speech. The pause is now 3.7–4.5 s (note 08 §10), not a minute — but four seconds of unexplained silence still tells a blind user nothing, so this stays an accessibility requirement rather than a latency workaround.
- `response_timeout_secs` on the `read_document` webhook can stay at the **20 s default** (range 5–300). A healthy read is 3.7–4.5 s (note 08 §10) and `LLM_TIMEOUT_MS=8000` expires first, so the backend still fails before the platform does and returns a speakable string.

---

# Section B — The 90-second demo script

> ## ✅ READ THIS BEFORE YOU REHEARSE — the 90 seconds fits a live read
>
> This script was written against a sub-8-second vision call. **That call exists.** The first round of live testing said otherwise — `docs/research/08-gemma-live-api-test-results.md` §6 measured 20–57 seconds and a 56.8 s vision call — but §6.1 and §10 showed those numbers belonged to `gemma-4-31b-it`. On the pinned `gemma-4-26b-a4b-it` the same three letters read in **3.7–4.5 seconds, 3/3 on the first attempt**, with `thinkingLevel: "minimal"` and zero thought characters.
>
> **The arithmetic, honestly.** The non-negotiable content is: the hook (~16s), start + greeting (~6s), raise and ask (~8s), the agent's spoken summary (~15s), the barge-in (~11s), the calendar card and `.ics` (~14s), the close (~8s) — **78 seconds before the model does anything at all.** A 4-second read overlapped by narration lands you at **≈1:22**, inside the slot. A single failed read and a retry costs you about another five seconds, not another minute: 26b went **19/19 with no 5xx** across §§6.1 and 10.
>
> **Verdict: run the 90-second script live, including the read.** Keep the one structural improvement the two-minute rework bought — start the read first and let the hook cover it — because it still removes the only pause in the demo. Do not cut the barge-in or the `.ics`, and do not mock the read: there is nothing left to hide. If you want a stub for a 30-second slot that is a scheduling decision, not a latency one, and it still has to be disclosed out loud.

## Before you stand up — the setup checklist

| | Item |
| --- | --- |
| ☐ | **`test-letters/01-hospital-appointment.png` printed on matte A4.** Matte, not gloss, not a phone screen — gloss throws a webcam-killing specular highlight under venue lighting, and a phone screen adds moiré and backlight bloom. Plain office paper is ideal. |
| ☐ | A **second printed copy** face-down on the table. Paper creases, and a crease across the date line is a demo-ender. |
| ☐ | Tunnel up, backend up, frontend up, **all three verified in the last 10 minutes** (tunnels die quietly). |
| ☐ | A **dry run completed on this venue's wifi and lighting**, not on your hotel wifi. |
| ☐ | Laptop volume at ~80%, **external speaker if the room is bigger than 20 people**. Laptop speakers do not carry, and the agent's voice is the entire product. |
| ☐ | **Backlight check:** no window or stage light directly behind you. Backlight is the #1 cause of an unreadable frame. |
| ☐ | Browser mic + camera permissions already granted, so no permission dialog eats five seconds. |
| ☐ | Everything else closed. One browser tab. |

**How to hold the letter:** both hands, thumbs at the bottom corners, roughly **30–40 cm from the lens**, letterhead **level with the top of the camera preview**, tilted back about 10° so the page faces the lens rather than the ceiling. Keep it still for a full two seconds after you stop talking — the frame is captured mid-sentence otherwise. Do not cover the date block with your thumbs.

## The script (read started first, narrated over)

Read the **SAYS** column verbatim. It is written to be read off a card by someone whose hands are shaking.

**The one structural change from the original script: you start the read before you deliver the hook.** The hook used to open the demo; it now *covers the vision call*. This is the only edit that buys real time, and it has a second benefit — the room hears the human story while the machine works, so the longest pause in the demo is also its most persuasive stretch.

Clock values below are the slack-budgeted version, written when a read took the better part of a minute. On the pinned model it takes **3.7–4.5 seconds** (note 08 §10), so the agent will normally start speaking at about **0:19–0:20 — in the middle of your hook.** That is the correct outcome, not a mistake: stop mid-sentence and let it talk. Everything from "the agent speaks" onwards **slides earlier with the read**, which is how 78 seconds of content plus a 4-second read comes in at ≈1:22. Rehearse the narration blocks anyway — they are what you reach for if the frame upload or the venue network is slow.

| Clock | You DO | You SAY (verbatim) | Audience SEES / HEARS |
| --- | --- | --- | --- |
| **0:00–0:06** | Turn to the laptop. Click **Start**. Hold the letter ready but out of frame. | *(say nothing — let the agent speak)* | **Agent, aloud:** "Hi, I'm LetterLens. Hold a letter up to the camera and I'll tell you what it says." A live transcript line appears. |
| **0:06–0:14** | Raise the letter into frame, both hands, 38–40 cm, letterhead at the top of the preview. **Hold perfectly still until the agent answers you.** | "I've got a letter from the hospital here — can you tell me what it says?" | The camera preview fills with the letter. The letterhead is legible on the projector. |
| **0:14** | — | — | **Agent, aloud:** *"Let me read that for you, one moment."* Tool-call sound, then a visible **Reading your letter…** state that stays up. **The clock that matters starts here.** |
| **0:14–0:20** | **Hold still two more full seconds**, then lower the letter slowly and turn to the room. The frame is captured once, at the start of the call — once the agent has spoken that line, the picture is already taken and your arms are free. | *(nothing yet — let that line land)* | The preview empties. The **Reading your letter…** state stays up, which is the point: the room can see it is working. |
| **0:20–0:36** | **THE HOOK. This is the bit that used to open the demo.** Talk to the room, not the laptop. Do not look at the screen. | "While that's working — this is a hospital appointment letter. If you're blind, this piece of paper is just an envelope that arrived. You find out what it says when someone sighted next comes round. Maybe Saturday. And this one says that if you miss two appointments, you get referred back to your GP." | A person telling a story. The *reading…* state ticking away behind them reads as *the product working*, not as a hang. |
| **0:36–0:48** | Still talking to the room. | "What it's doing right now is pulling one frame off the webcam and sending it to Gemma — the open-weights multimodal model, running on the Gemini API. It isn't transcribing the page. It's pulling out a structured object: who sent it, what they want, and the date." | Same state — or, more likely by now, the agent has already started speaking and you have stopped mid-sentence to let it. Keep this block ready rather than scripted. |
| **0:36–0:42** | **The measurement beat.** The read will normally have landed before this; use it only if you have a gap, and stop mid-sentence the moment the agent speaks. | "And the number here is measured, not guessed: the read comes back in about four seconds. Our first measurement said fifty-seven — then we held every other variable still and found that was the other Gemma model. Swapping one line of config beat redesigning the architecture." | A presenter who shows a number *and* how they checked it reads as competent. One who quotes a figure they never isolated does not. |
| **≈0:58–1:13** | Stop talking completely. Look at the audience, not the screen. | *(silence — this is the agent's moment, do not step on it)* | **Agent, aloud, ~40 words:** that it's from Mere Valley Hospital Trust, a dermatology appointment on Thursday the 6th of November at 10:40, arrive fifteen minutes early. A structured card renders alongside: sender, date, deadline. |
| **≈1:13–1:24** | **THE BARGE-IN.** As soon as the agent starts its *next* sentence — the one offering an action — talk straight over it. Do not wait for a gap. Normal volume. | "Sorry — what happens if I can't make it?" | **The agent stops mid-word.** Audible cut, not a fade. Then it answers: call the Booking Centre, at least five working days before. **This is the moment that wins the room.** Say nothing about it; let them notice. Note this answer comes back *fast* — it is a text turn on the same `gemma-4-26b-a4b-it`, ~2 s (note 08 §6.1). |
| **≈1:24–1:38** | Let the agent offer the action. Say yes. Click the download when the card appears. | "Yes please, put it in my calendar." | **Agent:** offers to add it. Then a **calendar card** renders with the 6 November 10:40 appointment and an **`.ics` download**. The file lands in the downloads bar — visible proof. |
| **≈1:38–1:46** | Hold up the printed letter one last time, next to the screen. | "Paper in, calendar entry out — and it didn't send anything, it just drafted it for her to confirm. That's the whole product." | Paper in one hand, calendar card on screen. Stop talking. |

<!-- TODO(human): confirm with your own backend that read_document captures ONE frame at the start of the call, so the presenter can lower the letter at 0:20 rather than holding A4 steady for the whole call. At 3.7–4.5 s this is much less painful than it was, but if the implementation re-captures or captures late, the 0:14–0:20 row is wrong and you must brace your elbows and hold throughout — in which case mount the letter on a clipboard or a stand. -->

### Budgeting the silence — two windows, and the first one is short again

1. **≈0:14–0:19, the vision call.** This was once budgeted at twelve seconds and briefly at thirty to sixty; measured on the pinned `gemma-4-26b-a4b-it` it is **3.7–4.5 s** (note 08 §10), and it is still *yours*. One short narration block covers it. Keep a second ready — not because the model is slow, but because the frame upload and TTS are not in the 4.5 s figure. **If the result lands mid-sentence, stop and let the agent talk** — the agent interrupting *you* is a good look, and at four seconds it will almost always happen.
   - **Never let this window go quiet.** The spoken "let me read that for you" at 0:14 and the persistent *Reading your letter…* state are what make even a four-second pause legible as work rather than as a crash. If `pre_tool_speech: "force"` is not set on the agent, that line may not play — and then you are standing in unexplained silence with nothing to point at.
2. **≈0:20–0:35, the agent speaking.** This silence belongs to the agent. **Do not narrate over it.** The single most common demo mistake is talking across your own product's best twelve seconds — and when it arrives mid-hook, the temptation to finish your sentence is at its strongest exactly when you must stop.

### If it breaks

One line per segment. Keep moving; never say "it worked earlier." Deeper failure-mode analysis and recovery procedures live in **`docs/demo-notes.md`** — read that before the event; do not try to debug from this table.

**First, the rule that governs this whole table.** A long silence is a symptom again. On the pinned `gemma-4-26b-a4b-it` a healthy read is **3.7–4.5 s** and the model went **19/19 with no 5xx** across note 08 §§6.1 and 10, so anything past about ten seconds is a config, tunnel or session problem rather than a slow model. **Pick your abandon time before you stand up — 15 seconds after the agent said "let me read that for you" — and obey it.** The discriminators are in `docs/demo-notes.md` §3.1a.

| Segment | If it breaks, say |
| --- | --- |
| 0:06 greeting never plays | "Let me reconnect — while that's coming up: this whole thing is one agent with six tools, two running on a server and two running right here in the browser." *(Refresh. Keep talking.)* |
| You run out of narration before the read lands (past ~0:25) | "I'm going to let that keep working while I tell you what's next for it —" *(then the "What's next" material: multi-page letters, a phone number, returning-sender memory. You have about another thirty seconds of it. This is why you prepared more words than you planned to use.)* |
| **15 seconds in and still nothing** | "That's not the model — a read comes back in about four seconds. Something upstream of it has gone. Let me give it a cleaner shot." *(Second printed copy, flatter, closer. **One** retry, then the recording.)* |
| Agent says it can't read the letter | "That's the behaviour I actually want you to see — it will not invent an appointment date. Let me flatten it out." *(Use the backup copy. This failure is a feature; sell it.)* |
| Agent starts reading a long rambling monologue about what it is thinking | *(Interrupt it immediately — barge-in is right there.)* "That's the model's scratchpad leaking through — one for the backlog." *(This is the unfiltered `thought: true` part. See `docs/demo-notes.md` §0.3. If this happens on stage the bug is in the backend, not the network, and no retry will fix it: go to the recording.)* |
| Barge-in doesn't cut it off | *(Don't flag it.)* Wait for the agent to finish, then: "And you can interrupt it at any point — watch." *(Try once more on the next sentence. If it fails again, move on. Never attempt a third time.)* |
| Calendar card / `.ics` doesn't render | "The `.ics` is generated in the browser, so there's no round trip — here's one from the run I did ten minutes ago." *(Have a pre-generated `.ics` open in a second tab. Prepare this before you present.)* |
| Total collapse, nothing works | "Right — the wifi's beaten me. Thirty seconds on what you'd have seen, and then come to the table and I'll run it for you one-to-one." *(Deliver the one-sentence version, then the 30-second version from memory. Do not debug on stage.)* |

## The 30-second cut-down

For when the organisers are running late.

> **A live read fits in thirty seconds.** On the pinned `gemma-4-26b-a4b-it` the three test letters read in **3.7–4.5 s**, 3/3 first attempt (note 08 §10); the 19.9 s floor and the 56.8 s vision call we first measured were `gemma-4-31b-it`. Run it live. Keep the mock (`?mock=1`, `docs/demo-notes.md` §3.3I) as a break-glass for a dead network, not as the plan — and if you do use it, say the word "stubbed" out loud once.

Drop the architecture narration and the barge-in setup; keep the paper, the voice, and the `.ics`.

| Clock | You DO | You SAY (verbatim) |
| --- | --- | --- |
| **0:00–0:06** | Hold up the letter. | "Hospital appointment letter. If you're blind, this is unreadable without sighted help — and it says missing two appointments gets you referred back to your GP." |
| **0:06–0:14** | Start the session, raise the letter, hold still. | "I've got a letter from the hospital — what does it say?" |
| **0:14–0:22** | Hold still, then lower it. | "It's reading the frame with Gemma — open-weights, multimodal. About four seconds, and that number is measured." *(then be quiet and let the agent summarise)* |
| **0:22–0:30** | Say yes to the action; show the download. | "Yes, put it in my calendar." *(card + `.ics` appears)* "Paper in, calendar entry out. Nothing sent — only drafted." |

**If the 30-second version breaks:** go straight to the one-sentence version and offer a one-to-one run at the table.

## The one-sentence version

For a judge walking past with a lanyard and no time:

> "LetterLens is a voice assistant for blind people dealing with paper post — you hold a hospital letter up to the webcam, it tells you who it's from and when the appointment is, and it puts it in your calendar."

If they slow down, the follow-up is: *"It's an ElevenLabs voice agent with a Gemma vision tool — and you can interrupt it mid-sentence. Want to try?"* Then hand them the letter. Letting a judge hold the paper themselves is worth more than any slide.

---

# Section C — Prize track arguments

## 1. Best Use of Gemma 4 (Google)

> ### ✅ RESOLVED — the model pin was wrong, and it is now fixed. One thing left to verify.
>
> **This was the top blocker on this document, and it no longer is.** Recording it in full, because the story is worth telling in the submission and because the remaining step is real.
>
> **What was wrong.** The track requires Gemma 4. `.env.example` pinned Gemma **3** — and worse, a model ID the Gemini API does not serve at all:
>
> ```
> GEMMA_MODEL=gemma-3-27b-it          # was
> GEMMA_VISION_MODEL=gemma-3-27b-it   # was
> ```
>
> **What the Gemini API actually serves.** `docs/research/01-gemma-on-gemini-api.md` §1 quotes the Supported Models section of `https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api` verbatim; `docs/research/08-gemma-live-api-test-results.md` §2 then confirmed it against the live `GET /v1beta/models` (50 models returned). The complete list is **two models**:
>
> | Served model ID | Shape | Modalities | Live status |
> | --- | --- | --- | --- |
> | `gemma-4-26b-a4b-it` | MoE, 25.2B total / **3.8B active** | **Text + Image** | **Served, and this is the pin. Text 8/8 at a 2.0 s median; vision 3/3 first attempt in 3.7–4.5 s, verbatim-correct on all three test letters (note 08 §§6.1, 10).** |
> | `gemma-4-31b-it` | Dense, 30.7B | **Text + Image** | Served, text and vision work — but **rejected**: 20–57 s with a ~50 % serial failure rate, and 36.8–56.8 s on vision (note 08 §§6, 10). Useful only as a second 30 RPM quota bucket. |
> | `gemma-3-27b-it` | — | — | **404 — does not exist.** |
>
> The 404 is verbatim: `{"error":{"code":404,"message":"models/gemma-3-27b-it is not found for API version v1beta, or is not supported for generateContent...","status":"NOT_FOUND"}}`. So the repo's defaults could never have worked on any request — this was never only an eligibility problem. The E2B / E4B / 12B Gemma 4 sizes are **open-weights only**; do not send those IDs to the Gemini API either.
>
> **The fix, already applied.** `.env.example` now reads:
>
> ```
> GEMMA_MODEL=gemma-4-26b-a4b-it
> GEMMA_VISION_MODEL=gemma-4-26b-a4b-it
> ```
>
> with an inline head-to-head citing note 08 §§6.1 and 10, and `LLM_TIMEOUT_MS=8000` unchanged. `CHAT_MODEL` and `VISION_TIMEOUT_MS` remain in the file commented out and explicitly marked **no longer needed** — they were staged for a split-path architecture that the 26b measurements retired.
>
> **Why `gemma-4-26b-a4b-it` and not the dense 31B.** Note 01 §8 recommended the MoE on the reasoning that ~3.8B active parameters would be fast; this document briefly overrode that on the strength of a vision call verified on `gemma-4-31b-it` (note 08 §3), with the MoE's speed advantage dismissed as confounded by a `maxOutputTokens: 1` cap. A controlled cross removed the confound — serial, concurrency 1, identical prompt, eight calls per cell (note 08 §6.1): **26b answered 8/8 in a 2.0 s median with thinking active and output uncapped, while 31b took 24.9 s on a single capped token.** §10 then closed the last gap: 26b read all three letters in **3.7–4.5 s, 3/3 first attempt, verbatim-correct**, against 31b's 36.8–56.8 s. Roughly 12× faster on text, ~10× on vision, and **19/19 with no failures**. Note 01 was right, and for the right reason. `gemma-4-31b-it` stays useful only as a second 30 RPM quota bucket, since the free-tier limit is per project *per model*.
>
> **What is still left to do.** The pin is right and the model demonstrably works, but the *backend does not exist yet*. Nobody has made a `read_document` call through the application stack. **Get one real 200 from `gemma-4-26b-a4b-it`, through the backend, with a camera frame, before submitting to this track.** The curl-level questions note 01 §9 raised are all settled now (base64 vision works; `responseSchema` is accepted and silently ignored) — what remains is proving the chain, not the model.
>
> <!-- TODO(human): once backend/ has a read_document handler, run it end to end against a live frame and confirm a 200 with a non-empty, non-scratchpad answer. That is the last thing standing between this track and a clean submission. -->

**The argument.** LetterLens is multimodal in the way the track asks for: a single Gemma 4 call takes an **image** of a physical letter and a **text** instruction and returns structured text — this is not an OCR step bolted to a separate language model, it is one multimodal pass doing recognition and comprehension together, which is exactly why it can tell you "they want you to call five working days before" rather than reading you a phone number. **And we can prove the pass works rather than asserting it:** note 08 §10 records live 200s from the pinned `gemma-4-26b-a4b-it` on all three of our own test letters — first attempt each, **3.7–4.5 s**, sender and date verbatim-correct against the known-good transcripts, including picking the reduced-amount deadline out of the parking penalty's two dates — for 258 image tokens on a full A4 page. It is a focused tool for a specific community, not a general-purpose demo: blind and low-vision people dealing with official paper post, tested against three letters drawn from the actual categories that matter — NHS, enforcement, school. On speed of prototyping: a one-day build, with model IDs pinned in env rather than hard-coded so the vision model is a one-line swap — which is precisely how we recovered in minutes when testing proved the original pin was a 404. And eight verified research notes, the last of which is live HTTP against a real key, meant we spent the day building against measured behaviour instead of guessing which API surface Gemma lives on. The part we would most want a Gemma judge to read is note 08 itself: it is an honest account of nearly redesigning a system around a latency that turned out to belong to the other model, and of the controlled test that caught it before any code was written.

## 2. Best Open-Source AI Project

This is our strongest track. **Open-weight AI is the functional core, not a garnish:** the entire comprehension step — the thing that turns a photograph of an NHS letter into `{doc_type, sender, key_dates, deadline, actions_required}` — runs on Gemma, Google's open-weights family, and if you remove it the product is a webcam with a microphone attached. The repo is **public at `https://github.com/llygrace034/vision-impairment-assistance` under the Apache License 2.0** (`LICENSE` at root, full text, OSI-approved). Beyond the application, LetterLens ships a reusable **Agent Skill** at `skills/letter-reader/SKILL.md`, authored against the **Agent Skill Open Standard** (agentskills.io) — frontmatter restricted to the six specified fields with `name` and `description` required, any version string nested under `metadata` as a quoted string rather than a top-level `version` key (the single most common validation failure, per `docs/research/06-agentskills-spec.md`), a directory name matching `name` exactly, and progressive disclosure via `references/`. That packaging matters for the track's spirit as much as its letter: the letter-reading behaviour is portable to any skill-aware agent rather than welded to our frontend. Finally, the **eight** research notes in `docs/research/` are themselves open output — each one cites primary sources with fetch dates and marks its own unconfirmed claims, which is the part of this repo most likely to be useful to someone else building on Gemma or ElevenLabs next week. Note 08 in particular is the thing we would most like someone to steal: a live-fire test report on Gemma via the Gemini API with real status codes, real latencies and a real failure rate, including the three findings that are not in anybody's documentation — `inline_data` base64 vision works, `responseSchema` is accepted and silently ignored, and the free tier feels completely different depending on which of the two Gemma models you pick — 20–57 s and a ~50 % serial failure rate on `gemma-4-31b-it`, 2.0 s and 8/8 on `gemma-4-26b-a4b-it`. That is a day somebody else does not have to spend.

<!-- TODO(human): confirm skills/letter-reader/SKILL.md exists and passes `skills-ref validate skills/letter-reader`. skills-ref is not on PyPI — clone github.com/agentskills/agentskills and `pip install -e skills-ref/`. Do not claim standard compliance in the submission form until it validates clean. -->
<!-- TODO(human): confirm the GitHub repo is public at submission time. It returned HTTP 200 unauthenticated on 2026-10-03, so it is public now — re-check if you touch repo settings. -->

## 3. Best Use of ElevenLabs

**Agentic depth and autonomous conversational capability:** LetterLens is not a TTS wrapper. The agent owns a six-tool inventory across three execution surfaces — two server tools reaching a Python backend over a webhook (`read_document`, `draft_reply`), two client tools executing in the browser (`add_event`, `set_reminder`), and two ElevenLabs system tools (`end_call`, `skip_turn`) — and it decides unprompted when to look, when to act, and when to stay quiet. It operates under hard autonomy constraints that are part of the design rather than a disclaimer: it must call `read_document` before making any claim about a letter, it offers exactly one next action rather than a menu, and it never sends anything on the user's behalf. **Interaction design and turn-taking:** barge-in is live and demoed, not described — interrupt it mid-sentence and it stops on the word, because the SDK flushes queued audio and a stale-audio guard drops any chunk predating the interruption, so it physically cannot resume the sentence you cut off. We tuned the silence as carefully as the speech: `pre_tool_speech: "force"` guarantees a spoken acknowledgement before the vision call, `tool_call_sound` gives the pause an audible floor, and `skip_turn` lets the agent deliberately say nothing while a user is still reading — which, for a blind user, is a feature rather than an absence. **Creative technical use of the API:** the client/server tool split is driven by real constraints — the Gemini key never reaches a browser, and the `.ics` is generated in-page with no round trip — and we authenticate server tools with a secret custom header after establishing from the docs that HMAC signing covers post-call webhooks, not mid-conversation tool calls. **Novelty and real-world impact in accessibility**, which the track names explicitly: this is not accessibility as a theme, it is a specific unsolved task for a specific group of people — a blind person who cannot read the hospital letter that says missing two appointments gets you referred back to your GP, and for whom a voice interface is not a convenience but the only interface.

## 4. Best Use of Openloft — *honest assessment: do not submit*

**LetterLens as built does not qualify, and I would not submit it to this track.** Openloft asks for neuromorphic associative memory that retains context across sessions for continuous learning and adaptation. LetterLens is deliberately **stateless across sessions**: a conversation ends, nothing persists, and that is a privacy posture rather than an oversight — the letters in question are medical and financial, and "we remember everything you showed us" is the wrong default for a product handling someone's dermatology referral. Entering this track would mean claiming a capability the repo does not contain, and a judge who opens the repo will see that in about ninety seconds. **If you want it anyway, here is the smallest honest version:** persist a per-user index of sender fingerprints and the letter objects already extracted, and associate each new letter with prior ones from the same sender — so the agent can open with *"this is the third letter from Mere Valley Hospital this month; the last one was an appointment you added to your calendar on the 6th"*, and can flag an escalation (a reminder letter about a penalty you already saw). That is genuinely associative recall over a growing store, and for someone who cannot visually scan a pile of post it is a real feature, not a track-shaped bolt-on. But it is a feature, with a storage model and a consent flow attached, and it does not exist today. <!-- TODO(human): decide — skip this track (recommended), or build sender-association memory and only then claim it. Do not submit the current build to Openloft. -->

## 5. Hackiest Hack (Hackathons UK)

Consider what is actually happening here. A conversational AI in the cloud needs to know what is on a piece of paper, so it calls a webhook, which travels down a tunnel held open by a free-tier ngrok process, to a laptop under a table in Bradford, which grabs a frame off the same webcam you use for standups, and hands a JPEG of someone's dermatology appointment to a thirty-billion-parameter language model, which reads it, in a 256K context window, in order to produce roughly eleven words of plain English and a 400-byte `.ics` file. It takes **four and a half seconds**. We know that because we timed it, and we know what it cost to find out: our first measurement said fifty-seven seconds, and the model had written four thousand two hundred and thirty-six characters of private deliberation — including, verbatim, *"Wait, maybe they want the first sentence of the message?"* — in order to emit five tokens. One `thinkingLevel: "minimal"` and one swap to the other Gemma model took that to zero characters and four seconds, which is the single highest-leverage config change any of us has made this year. We still filter `thought: true` parts, because otherwise our assistant for blind people reads its own diary aloud to them. The number of distributed systems participating in the sentence "it's on the sixth of November at twenty to eleven" is genuinely upsetting, and the amount of *thinking* participating in it is worse. Six tools across three execution surfaces, two of which are someone else's infrastructure, and exactly one language model, because we very nearly shipped two and then measured properly. Authentication is a shared secret in a header, because we read the docs properly and discovered the HMAC we'd assumed existed does not. The whole thing is one `cloudflared` process away from total silence, and the demo script contains the phrase "if it breaks" four times. It is, however, string of the finest quality — every load-bearing claim has a research note with a URL and a fetch date behind it, and the one that mattered most has HTTP status codes. We would like the Blåhaj. We have earned the Blåhaj.

---

# Section D — Submission checklist

Work top to bottom. Nothing below is optional for the track it belongs to.

## Blockers — do these first

| ☐ | Item | Status / notes |
| --- | --- | --- |
| ☑ | ~~Change `GEMMA_MODEL` and `GEMMA_VISION_MODEL` off `gemma-3-27b-it`~~ | ✅ **DONE.** Both are now `gemma-4-26b-a4b-it` in `.env.example`, with an inline head-to-head citing note 08 §§6.1 and 10. The old pin was a hard 404, not just a track-eligibility problem. **Check `.env.local` matches** — that file is not readable from here. |
| ☑ | ~~Confirm a real 200 from the pinned model with an actual letter image~~ | ✅ **DONE at the API level.** `docs/research/08-gemma-live-api-test-results.md` §10: live 200s from `gemma-4-26b-a4b-it` on all three letters in `test-letters/`, first attempt each, 3.7–4.5 s, verbatim-correct against the known-good transcripts, 258 image tokens per page. `inline_data` base64 works — the Files API is not needed. |
| ☐ | **Get one real 200 through the *backend*, not just curl** | ⚠️ **NOT DONE — this is now the top Gemma-track blocker.** The model works; the application path to it does not exist yet. Needs a `read_document` handler, a captured frame, and a non-empty answer with `thought: true` parts filtered out. |
| ☑ | ~~Implement the split model paths~~ | ✅ **NOT NEEDED — DO NOT BUILD.** Note 08 §10 retired it: on `gemma-4-26b-a4b-it` text is 2.0 s median (8/8) and vision 3.7–4.5 s (3/3), so one model serves both paths inside `LLM_TIMEOUT_MS=8000`. `CHAT_MODEL` and `VISION_TIMEOUT_MS` stay commented out in `.env.example`, marked no longer needed. Re-evaluate only if the pin changes back. |
| ☐ | **Filter `thought: true` parts in the backend** | ⚠️ **NOT DONE — and this is a demo-killer, not a polish item.** Naive `parts[0].text` extraction returns a 4,236-character reasoning scratchpad, which the agent will then read aloud to a blind user as if it were the letter. Note 08 §4 gives the three-line fix. |
| ☐ | **Parse the vision response defensively** | `responseMimeType` + `responseSchema` return 200 and are **silently ignored** — the body comes back as markdown-fenced JSON that `json.loads()` chokes on. Strip fences, then validate the shape in Pydantic. Note 08 §5. |
| ☐ | **Serial requests + retries + honour `RetryInfo.retryDelay`** | Still do all three, but budget for the right failure: the ~50 % serial failure rate and the 26/40 `500`s were `gemma-4-31b-it`. On the pinned 26b, 40 requests at 8-way concurrency returned **zero** 5xx and 19/19 succeeded across §§6.1 and 10 — so expect 429s, not 500s. Serial is still safest, retries are still mandatory, and the advertised `retryDelay` is a floor (advertised 17s, real recovery 22.8s). Note 08 §§1.1, 6.1, 7. |
| ☐ | **Rewrite `README.md`** | 🔄 **IN PROGRESS, by another hand.** It was one line (`# vision-impairment-assistance`) and is being rewritten now; the rewrite pins `gemma-4-26b-a4b-it`, carries the `thought: true` hazard and the silently-ignored `responseSchema` finding, and records the split model path as superseded by note 08 §10. **Out of scope for this file — verify it before submitting, since it is a judge's first click.** |
| ☐ | **Confirm `skills/letter-reader/SKILL.md` exists and validates** | Directory exists; `SKILL.md` is being written concurrently. Required for the Open-Source track's Agent Skill clause. |

## Repo and licensing

| ☐ | Item | Status |
| --- | --- | --- |
| ☐ | Repo public on GitHub | ✅ `https://github.com/llygrace034/vision-impairment-assistance` returned HTTP 200 unauthenticated on 2026-10-03. Re-check if you change settings. |
| ☐ | OSI-approved license at root | ✅ Apache License 2.0, full text, `LICENSE`. |
| ☐ | License named in the submission form | Say "Apache-2.0" explicitly — the Open-Source track asks for it. |
| ☐ | **Keys not committed** | ✅ `.gitignore` line 23 (`*.local`) matches `.env.local` — confirmed with `git check-ignore -v`. `git ls-files` shows only `.env.example` tracked. **No change made or needed.** |
| ☐ | Double-check no key ever landed in history | `git log -p -- .env.local` should return nothing. Run it; a key in an earlier commit survives a later `.gitignore`. |
| ☐ | Work merged to `main` before submitting | Current HEAD is on `research-elevenlabs-sdk-and-agent-creation`. Branches `letterlens-scaffold-and-research` and `research-elevenlabs-sdk-and-agent-creation` exist on origin. **Judges will clone `main`.** |

## Build state

| ☐ | Item | Status |
| --- | --- | --- |
| ☐ | Backend has an actual entrypoint | ⚠️ `backend/` contains **only `requirements.txt`** as of writing. Needs the FastAPI app, the `read_document` and `draft_reply` webhook handlers, and secret-header verification. |
| ☐ | Frontend is not the Vite scaffold | ⚠️ `frontend/src/App.tsx` is still the **default Vite + React starter** (the counter button and the Vite/React logos). Needs the ElevenLabs session, camera preview, and the letter/calendar cards. |
| ☐ | ElevenLabs SDK actually installed | ⚠️ `frontend/package.json` dependencies are only `react` and `react-dom`. No `@elevenlabs/react`. |
| ☐ | `index.html` `<title>` says LetterLens | ⚠️ currently `frontend` — it is on screen during the demo. |
| ☐ | End-to-end run completed at least once | <!-- TODO(human) --> |

## ElevenLabs agent config (dashboard / agent JSON, not `.env`)

| ☐ | Item | Why |
| --- | --- | --- |
| ☐ | `interruption` enabled under **Client Events** | **Without it barge-in silently does not work** and the demo's best moment dies. Note 04 §7.1. |
| ☐ | System prompt in the dashboard matches `agent/persona-prompt.md` | The repo is declared authoritative; keep them in sync. |
| ☐ | First message set to the scripted greeting | Verbatim from `agent/persona-prompt.md`. |
| ☐ | `read_document` → `tool_error_handling_mode: "summarized"` | Default `auto` **hides** webhook errors from the agent, which then hallucinates success. Note 03 §7.3. |
| ☐ | `read_document` → `pre_tool_speech: "force"` | Guarantees spoken cover for the vision pause. |
| ☐ | `read_document` → `interruption_mode: "allow"` (the default) | Keep the user able to interrupt during the tool call. Note 03 §7.4. |
| ☐ | `read_document` webhook `response_timeout_secs` — **the 20s default is fine** | A healthy read is 3.7–4.5s on the pinned `gemma-4-26b-a4b-it` (note 08 §10), and `LLM_TIMEOUT_MS=8000` expires first, so the backend still fails before the platform does and returns a speakable string. The ≥120s figure in earlier drafts was derived from `gemma-4-31b-it`'s 19.9–56.8s and is superseded. |
| ☐ | Every tool's `response_timeout_secs` left at 20s | Every path runs on `gemma-4-26b-a4b-it` against `LLM_TIMEOUT_MS=8000`, which must expire first. The 20s default is correct everywhere. |
| ☐ | Secret header configured on the webhook tool, matching `TOOL_WEBHOOK_SECRET` | Note 03 §6. |
| ☐ | `add_event` / `set_reminder` registered as **client** tools with handlers in the browser | Note 03 §5. |

## Demo and media

| ☐ | Item | Notes |
| --- | --- | --- |
| ☐ | **Rehearse the 90-second script with a live read** | A live read is 3.7–4.5s on the pinned model (note 08 §10), so 90 seconds is achievable with one and no A/B/C choice is needed. Keep the "start the read first, narrate over it" ordering — it still removes the only pause — and no longer ask the organisers for extra time. |
| ☐ | **Rehearse with a stopwatch against a real read, three times** | You still want your own end-to-end p50 — note 08's 3.7–4.5s is the model call only, and excludes frame upload, your retry and ElevenLabs TTS. One narration block should cover it; keep a second in reserve for the parts the measurement does not include. |
| ☐ | Demo video recorded | <!-- TODO(human): confirm whether the MLH submission form requires a video and its max length — the form is the only authority. Record one regardless; judges rewatch. A live read fits a short cut now (3.7–4.5s, note 08 §10), so record it live rather than stubbed. --> |
| ☐ | Video shows the **barge-in** and the **`.ics` download** | The two moments that prove it is an agent, not a narrator. |
| ☐ | `test-letters/01-hospital-appointment.png` printed on **matte A4**, twice | Section B setup checklist. |
| ☐ | Tunnel URL live and `PUBLIC_BASE_URL` current | Tunnel URLs change on restart. Re-verify within 10 minutes of demoing. |
| ☐ | Dry run on **venue** wifi and lighting | Not your hotel wifi. |
| ☐ | Pre-generated `.ics` open in a second tab as a fallback | Per the "if it breaks" table. |
| ☐ | `docs/demo-notes.md` read before presenting | Failure modes and recovery live there. |

## The form itself

| ☐ | Item |
| --- | --- |
| ☐ | Product name entered as **LetterLens** everywhere (the repo directory is `vision-impairment-assistance`; mention it once so judges aren't confused by the URL) |
| ☐ | Section A pasted under the matching form headings |
| ☐ | Tracks selected: **Gemma 4** (pin is fixed; confirm one real 200 through the backend first), **Open-Source AI**, **ElevenLabs**, **Hackiest Hack**. **Not Openloft** — see Section C.4 |
| ☐ | Repo link, demo video link, and license named in the form |
| ☐ | Every `TODO(human)` in this file resolved |

---

# Recommendations for files I did not touch

My scope was this file only. These are recommendations, not changes — I created, edited and deleted nothing else.

1. **`.env.example` — ✅ already done.** Both Gemma pins are now `gemma-4-26b-a4b-it`, with the note 08 §§6.1/10 head-to-head inline, `LLM_TIMEOUT_MS=8000` unchanged, and the split-path variables (`CHAT_MODEL`, `VISION_TIMEOUT_MS`) left commented out and marked no longer needed. **Still yours:** confirm `.env.local` carries the same pins. I did not read `.env.local` and no key value appears anywhere in this file.
2. **Backend — four non-negotiables from note 08**, in priority order: filter `thought: true` parts (§4), strip markdown fences before `json.loads` and validate server-side (§5), issue requests strictly serially with mandatory retries honouring `RetryInfo.retryDelay` as a *floor* (§§1.1, 6), and keep every path on the one pinned Gemma model inside `LLM_TIMEOUT_MS=8000` — §7 option 1 is superseded by §10. The first of those is the one that embarrasses you on stage.
3. **`README.md` — being rewritten by another hand.** Out of scope here; it already agrees with note 08 on the pin, the thought-part hazard and the split path. Worth a read-through before submitting.
4. **`frontend/index.html` — set `<title>` to `LetterLens`.** It is currently `frontend`, and it will be on the projector.
5. **`agent/persona-prompt.md` — consider adding an explicit failure instruction.** Research note 03 §7.3 is clear that what the agent says on tool failure is governed by the prompt, and no canned phrase is documented. Something like: *"If `read_document` fails or returns low confidence, say you couldn't read it clearly and ask the user to flatten the letter or hold it closer. Never summarise a letter you could not read."* The operating rules already state this in prose; it is not in the prompt text itself. **Add a second line for the wait**, even though a read is now 3.7–4.5 seconds (note 08 §10): *"Before calling `read_document`, always say you are going to read it and ask the user to wait a moment."* Four seconds of silence tells a sighted user "it's thinking" and a blind user nothing.
6. **Merge to `main` before submission.** Judges clone the default branch.
