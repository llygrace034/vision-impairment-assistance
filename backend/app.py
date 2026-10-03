"""LetterLens MVP backend.

Two jobs only:

1. `GET /signed-url` mints a short-lived ElevenLabs conversation token so the
   browser never sees `ELEVENLABS_API_KEY`.
2. `POST /read_document` takes one camera frame and returns a faithful plain-text
   reading of the letter, which the agent then summarises in its own voice.

`read_document` is wired as an ElevenLabs **client** tool, not a webhook tool, so
the browser calls this endpoint directly with the frame it already holds. That
removes the frame-upload correlation problem and with it ngrok, PUBLIC_BASE_URL
and TOOL_WEBHOOK_SECRET. See docs/research/03 section 5.
"""

from __future__ import annotations

import base64
import os
import time

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# .env.local holds the real secrets and overrides .env.example.
load_dotenv(".env.local")
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
VISION_MODEL = os.getenv("GEMMA_VISION_MODEL", "gemma-4-26b-a4b-it")
# Used only when the primary model fails (5xx, or timeout). Measured on
# 2026-10-03: gemma-4-26b-a4b-it returned HTTP 500 "Internal error encountered"
# or timed out on four consecutive frames it had read correctly minutes before,
# while gemini-flash-latest read the same frames in 2.6-3.3s. Set it to "" to
# disable. A demo must not depend on one upstream model having a good minute.
VISION_FALLBACK_MODEL = os.getenv("VISION_FALLBACK_MODEL", "gemini-flash-latest")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]

# Free-tier Gemini latency is wide, not tight: the same 1024px letter measured
# 5.1, 5.5, 8.2, 14.4 and 30.5s across five consecutive calls. So this is a
# tail-latency problem, not an average one, and a 25s cap would have turned the
# slowest call into an error instead of an answer.
#
# httpx's `timeout=` is per-operation, not total, so a slow trickling response
# can outlive it -- the 30.5s call did exactly that under a nominal 25s. Bound
# the whole request explicitly instead, and keep that bound under the client
# tool's response_timeout_secs (120) so the backend is always the thing that
# gives up first and can hand back a sentence the agent can speak.
VISION_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Plain text, not JSON -- but NOT for the reason note 08 section 5 gives.
# Re-measured live against gemma-4-26b-a4b-it on 2026-10-03:
#   * the union-type form in skills/letter-reader/references/output-schema.md,
#     {"type": ["string", "null"]}, is HARD REJECTED with HTTP 400
#     'Proto field is not repeating, cannot start list' -- not ignored; and
#   * {"type": "string", "nullable": true} IS honoured: unfenced JSON that
#     json.loads() parses directly, using the requested field names.
# So structured output does work, and note 08 section 5 is wrong on this.
# We still send plain text, because latency is dominated by output tokens:
# the full ~200-460 token letter object measured p50 12.4s (max 26.2s)
# against 4.3-5.4s for the six lines below. In a voice demo that difference
# is the product. The agent does the summarising either way.
#
# A FULL reading, not a fixed field list. The six-line letter schema this
# replaces (FROM/ABOUT/WHEN/DEADLINE/REF/CONTACT) was 3.8-4.4s but it discards
# anything without a slot, which is fatal once the documents stop being letters.
# Measured live against this backend on 2026-10-03: a pharmacy receipt lost
# every line item, a cafe menu lost every price, and a medicine label lost its
# entire dosage -- "take ONE capsule THREE times a day for 7 days" came back
# nowhere, which is the one thing on the page that matters.
#
# The target documents are now flyers, adverts, project and task instructions,
# A4 instruction sheets and paediatric patient case cards. Those share no common
# field set at all, so there is no schema to write. A faithful transcription is
# the only shape that serves all of them.
#
# This is also a CONVERSATION, not a one-shot summary: the agent answers every
# follow-up from this text and never gets a second look at the page, so whatever
# the reading drops is permanently unanswerable. Paying the latency once buys
# every subsequent question for free.
#
# Cost, from the structured-output measurements above: p50 12.4s, max 26.2s,
# against VISION_TIMEOUT's 60s and the client tool's response_timeout_secs of
# 120. The tail fits with room to spare.
#
# `[unclear]` earns its place. Without it the model fills gaps with plausible
# values -- a shifted dose, a transposed digit -- and a user who cannot see the
# page has no way to catch it. An admitted gap is recoverable; a confident wrong
# number read aloud is not.
READ_PROMPT = (
    "Read this document for a voice assistant that will answer questions about "
    "it. Transcribe every piece of text you can see, in the order it appears, "
    "keeping the structure: headings, labelled fields, lists and tables.\n"
    "Begin with one line: TYPE: <what kind of document this is, under 8 words>\n"
    "Then the reading itself. Rules:\n"
    "- Copy every name, date, time, number, dose, amount, phone number and "
    "reference code EXACTLY as printed. Never round, reformat or infer a digit.\n"
    "- Keep each instruction complete, including how much, how often, how long "
    "and in what order.\n"
    "- For a labelled field that is printed but empty, write the label then "
    "(blank).\n"
    "- Where text is cut off, covered or illegible, write [unclear] at that "
    "exact spot. Never substitute a plausible value for one you cannot read.\n"
    "- Add no advice, diagnosis, summary or opinion of your own.\n"
    "If the whole image is too blurry, dark or cut off to read, reply with "
    "exactly: UNREADABLE"
)

app = FastAPI(title="LetterLens MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Preflight for the demo: shows which keys are actually loaded."""
    return {
        "ok": True,
        "gemini_key": bool(GEMINI_API_KEY),
        "elevenlabs_key": bool(ELEVENLABS_API_KEY),
        "agent_id": ELEVENLABS_AGENT_ID or None,
        "vision_model": VISION_MODEL,
    }


@app.get("/signed-url")
async def signed_url() -> dict:
    """Mint a single-use conversation token for the browser."""
    if not (ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID):
        raise HTTPException(500, "ELEVENLABS_API_KEY or ELEVENLABS_AGENT_ID is not set")

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            "https://api.elevenlabs.io/v1/convai/conversation/token",
            params={"agent_id": ELEVENLABS_AGENT_ID},
            headers={"xi-api-key": ELEVENLABS_API_KEY},
        )
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs token request failed ({r.status_code}): {r.text[:200]}")
    return {"token": r.json()["token"]}


def _extract_text(payload: dict) -> str:
    """Join the non-thought text parts of a generateContent response.

    Gemma 4 is a thinking model and returns reasoning as a separate part flagged
    `thought: true`. That text must never reach the speaker: it ran up to 4,236
    characters against a 5-token answer in testing (research note 08 section 4).
    `thinkingLevel: "minimal"` already drives it to zero; this filter is the
    second layer, because a spoken-aloud leak is the worst failure in this demo.
    """
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "\n".join(
        p["text"] for p in parts if p.get("text") and not p.get("thought")
    ).strip()


@app.post("/read_document")
async def read_document(image: UploadFile = File(...)) -> dict:
    """Vision pass over one camera frame. Returns text for the agent to speak."""
    if not GEMINI_API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY is not set")

    raw = await image.read()
    if not raw:
        raise HTTPException(400, "empty image upload")

    body = {
        "contents": [
            {
                "parts": [
                    {"text": READ_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": image.content_type or "image/jpeg",
                            "data": base64.b64encode(raw).decode(),
                        }
                    },
                ]
            }
        ],
        # Keeps reasoning out of the spoken answer at the source.
        "generationConfig": {"thinkingConfig": {"thinkingLevel": "minimal"}},
    }

    started = time.monotonic()
    models = [VISION_MODEL] + ([VISION_FALLBACK_MODEL] if VISION_FALLBACK_MODEL else [])
    r = None
    used = VISION_MODEL
    error: str | None = None
    # The primary gets a shorter budget when a fallback exists, so that a
    # Gemma stall still leaves time for the fallback inside the client tool's
    # 120s window and the user's patience.
    primary_timeout = httpx.Timeout(30.0, connect=10.0) if len(models) > 1 else VISION_TIMEOUT
    for i, model in enumerate(models):
        used = model
        req = dict(body)
        if not model.startswith("gemma-4"):
            # thinkingLevel is a Gemma 4 field; other models reject or ignore it.
            req = {k: v for k, v in body.items() if k != "generationConfig"}
        try:
            async with httpx.AsyncClient(timeout=primary_timeout if i == 0 else VISION_TIMEOUT) as client:
                r = await client.post(
                    GEMINI_URL.format(model=model),
                    headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
                    json=req,
                )
        except httpx.TimeoutException:
            r = None
            error = f"{model}: timeout"
            continue
        if r.status_code == 200:
            break
        error = f"{model}: {r.status_code}: {r.text[:200]}"
        if r.status_code < 500 and r.status_code != 429:
            break  # a 4xx is our bug, not the model having a bad minute

    elapsed = round(time.monotonic() - started, 2)

    if r is None:
        # Never raise into the agent: a 5xx makes it apologise vaguely. Hand back
        # a sentence it can usefully say out loud instead.
        return {
            "text": "I could not read that in time. Please hold the letter still and try again.",
            "error": error,
            "elapsed_s": elapsed,
        }

    if r.status_code != 200:
        return {
            "text": "I had trouble reading that. Please try again.",
            "error": error,
            "elapsed_s": elapsed,
        }

    text = _extract_text(r.json())
    if not text or text.strip().upper().startswith("UNREADABLE"):
        return {
            "text": "I cannot quite make that out. Hold the letter a little closer and flatten it for me.",
            "elapsed_s": elapsed,
        }

    return {"text": text, "elapsed_s": elapsed, "model": used}
