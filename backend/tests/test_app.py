"""Offline contract tests for the LetterLens backend.

The contract these lock down is mostly about failure. LetterLens is a voice
product for blind users, so the two things that actually matter are that the
model's own reasoning never reaches the speaker, and that an upstream failure
arrives as a sentence the agent can say out loud rather than as a 5xx the agent
can only apologise vaguely about. Every outbound call is mocked with respx and
every config global is monkeypatched, so the suite needs no network, no API key
and no .env.local.
"""

from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx

from .conftest import (
    ELEVENLABS_TOKEN_URL,
    GEMINI_TEST_MODEL,
    GEMINI_FALLBACK_URL,
    GEMINI_TEST_URL,
    gemini_payload,
    text_payload,
)

SIX_LINE_READING = (
    "FROM: Leeds Teaching Hospitals NHS Trust\n"
    "ABOUT: Outpatient dermatology appointment confirmation\n"
    "WHEN: 14 November 2025 at 10:40am\n"
    "DEADLINE: NONE\n"
    "REF: 4471-9920-LD\n"
    "CONTACT: 0113 243 2799"
)


# --------------------------------------------------------------------------
# /health
# --------------------------------------------------------------------------


def test_health_reports_loaded_keys_and_pinned_model(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["gemini_key"] is True
    assert body["elevenlabs_key"] is True
    assert body["agent_id"] == "test-agent-id"
    assert body["vision_model"] == GEMINI_TEST_MODEL


def test_health_reports_false_for_unset_keys(client, appmod, monkeypatch):
    """The demo preflight has to be able to *fail*, not just say ok."""
    monkeypatch.setattr(appmod, "GEMINI_API_KEY", "")
    monkeypatch.setattr(appmod, "ELEVENLABS_API_KEY", "")
    monkeypatch.setattr(appmod, "ELEVENLABS_AGENT_ID", "")
    body = client.get("/health").json()
    assert body["gemini_key"] is False
    assert body["elevenlabs_key"] is False
    assert body["agent_id"] is None


def test_health_never_echoes_a_key_value(client):
    """Nothing in /health may be the secret itself, only a boolean about it."""
    raw = client.get("/health").text
    assert "test-gemini-key" not in raw
    assert "test-elevenlabs-key" not in raw


# --------------------------------------------------------------------------
# /signed-url
# --------------------------------------------------------------------------


@respx.mock
def test_signed_url_returns_token(client):
    route = respx.get(ELEVENLABS_TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"token": "conv-token-abc123"})
    )
    r = client.get("/signed-url")
    assert r.status_code == 200
    assert r.json() == {"token": "conv-token-abc123"}
    assert route.called
    sent = route.calls.last.request
    assert sent.url.params["agent_id"] == "test-agent-id"
    assert sent.headers["xi-api-key"] == "test-elevenlabs-key"


@pytest.mark.parametrize("missing", ["ELEVENLABS_API_KEY", "ELEVENLABS_AGENT_ID"])
def test_signed_url_500_when_elevenlabs_config_missing(client, appmod, monkeypatch, missing):
    monkeypatch.setattr(appmod, missing, "")
    r = client.get("/signed-url")
    assert r.status_code == 500
    assert "ELEVENLABS_API_KEY or ELEVENLABS_AGENT_ID is not set" in r.json()["detail"]


@respx.mock
def test_signed_url_502_carries_upstream_status(client):
    respx.get(ELEVENLABS_TOKEN_URL).mock(
        return_value=httpx.Response(401, text="unauthorized: bad xi-api-key")
    )
    r = client.get("/signed-url")
    assert r.status_code == 502
    detail = r.json()["detail"]
    assert "401" in detail
    assert "unauthorized" in detail


@respx.mock
def test_signed_url_502_on_upstream_500(client):
    respx.get(ELEVENLABS_TOKEN_URL).mock(return_value=httpx.Response(500, text="boom"))
    r = client.get("/signed-url")
    assert r.status_code == 502
    assert "500" in r.json()["detail"]


# --------------------------------------------------------------------------
# /read_document -- happy path
# --------------------------------------------------------------------------


@respx.mock
def test_read_document_returns_model_text_and_elapsed(client, image_file):
    route = respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(200, json=text_payload(SIX_LINE_READING))
    )
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == SIX_LINE_READING
    assert isinstance(body["elapsed_s"], (int, float))
    assert body["elapsed_s"] >= 0
    assert route.called


@respx.mock
def test_read_document_posts_the_frame_inline_to_the_pinned_model(client, image_file, jpeg_bytes):
    """The frame must go up as base64 inline_data against the pinned model."""
    route = respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(200, json=text_payload("FROM: Someone"))
    )
    client.post("/read_document", files=image_file)
    req = route.calls.last.request
    assert GEMINI_TEST_MODEL in str(req.url)
    assert req.headers["x-goog-api-key"] == "test-gemini-key"
    sent = json.loads(req.content)
    parts = sent["contents"][0]["parts"]
    assert "UNREADABLE" in parts[0]["text"]  # the prompt's blurry-image escape hatch
    inline = parts[1]["inline_data"]
    assert inline["mime_type"] == "image/jpeg"
    assert base64.b64decode(inline["data"]) == jpeg_bytes
    # thinkingLevel minimal is the first layer of the thought-leak defence.
    assert sent["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "minimal"


# --------------------------------------------------------------------------
# /read_document -- THE thought-leak test
# --------------------------------------------------------------------------


@respx.mock
def test_read_document_strips_thought_parts(client, image_file):
    """A part flagged `thought: true` must never reach the response.

    app.py's `_extract_text` docstring: Gemma 4's reasoning ran to 4,236
    characters against a 5-token answer in testing. This is a voice product, so
    a leak means the agent reads its own chain of thought aloud to a blind user.
    Assert the reasoning is ABSENT, not merely that the answer is present.
    """
    thought = (
        "Let me think about this step by step. The user wants me to read a letter. "
        "First I will examine the header region for a sender. I see what may be an "
        "NHS logo. Hmm, wait, let me reconsider the date format. " * 12
    )
    route = respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(
            200,
            json=gemini_payload(
                {"text": thought, "thought": True},
                {"text": SIX_LINE_READING},
            ),
        )
    )
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    text = r.json()["text"]
    assert thought not in text
    assert "step by step" not in text
    assert "let me reconsider" not in text.lower()
    assert text == SIX_LINE_READING
    assert route.called


@respx.mock
def test_read_document_strips_thought_part_that_arrives_last(client, image_file):
    """Part order must not matter -- the flag is the only thing that decides."""
    respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(
            200,
            json=gemini_payload(
                {"text": SIX_LINE_READING},
                {"text": "Actually on reflection the reference might be wrong.", "thought": True},
            ),
        )
    )
    text = client.post("/read_document", files=image_file).json()["text"]
    assert "on reflection" not in text
    assert text == SIX_LINE_READING


@respx.mock
def test_read_document_thought_only_response_is_treated_as_unreadable(client, image_file):
    """If reasoning is all there is, say the retry line -- never speak the reasoning."""
    respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(
            200,
            json=gemini_payload({"text": "I need to think harder about this.", "thought": True}),
        )
    )
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    text = r.json()["text"]
    assert "think harder" not in text
    assert "closer" in text.lower()


# --------------------------------------------------------------------------
# /read_document -- failures must arrive as speakable sentences, not 5xx
# --------------------------------------------------------------------------


@respx.mock
def test_read_document_upstream_timeout_is_200_with_a_speakable_sentence(client, image_file):
    """A 5xx makes the agent apologise vaguely; a sentence it can say is the design."""
    respx.post(GEMINI_TEST_URL).mock(side_effect=httpx.TimeoutException("read timed out"))
    respx.post(GEMINI_FALLBACK_URL).mock(side_effect=httpx.TimeoutException("fallback timed out"))
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    body = r.json()
    assert "text" in body
    assert body["text"].strip()
    assert "try again" in body["text"].lower()


@respx.mock
def test_read_document_upstream_read_timeout_subclass_is_caught(client, image_file):
    """httpx raises ReadTimeout in practice; it must hit the same branch."""
    respx.post(GEMINI_TEST_URL).mock(side_effect=httpx.ReadTimeout("the 30.5s tail call"))
    respx.post(GEMINI_FALLBACK_URL).mock(side_effect=httpx.ReadTimeout("fallback too"))
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    assert "try again" in r.json()["text"].lower()


@pytest.mark.parametrize("status", [400, 403, 429, 500, 503])
@respx.mock
def test_read_document_gemini_non_200_is_200_with_a_speakable_sentence(client, image_file, status):
    respx.post(GEMINI_TEST_URL).mock(return_value=httpx.Response(status, text="upstream said no"))
    fallback = respx.post(GEMINI_FALLBACK_URL).mock(
        return_value=httpx.Response(status, text="fallback said no")
    )
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    body = r.json()
    assert "text" in body
    assert "trouble reading that" in body["text"].lower()
    assert str(status) in body["error"]
    assert "elapsed_s" in body
    # A 4xx is our request's fault and must not be retried on another model;
    # a 5xx or 429 is the model having a bad minute and must be.
    assert fallback.called == (status >= 500 or status == 429)


@pytest.mark.parametrize("primary", ["500", "timeout"])
@respx.mock
def test_read_document_falls_back_when_the_primary_model_fails(client, image_file, primary):
    """Measured 2026-10-03: Gemma returned 500 / timed out on frames it had just
    read; the fallback must answer with real text, and say which model did."""
    if primary == "timeout":
        respx.post(GEMINI_TEST_URL).mock(side_effect=httpx.ReadTimeout("stalled"))
    else:
        respx.post(GEMINI_TEST_URL).mock(return_value=httpx.Response(500, text="Internal error"))
    fallback = respx.post(GEMINI_FALLBACK_URL).mock(
        return_value=httpx.Response(200, json=gemini_payload({"text": "TYPE: Receipt. TOTAL GBP 3.65"}))
    )
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    body = r.json()
    assert body["text"].startswith("TYPE: Receipt")
    assert body["model"] == "fallback-test-model"
    assert fallback.called
    # Non-Gemma models must not receive the Gemma-only thinkingConfig.
    sent = json.loads(fallback.calls.last.request.content)
    assert "generationConfig" not in sent


@respx.mock
def test_read_document_no_fallback_when_disabled(client, appmod, monkeypatch, image_file):
    monkeypatch.setattr(appmod, "VISION_FALLBACK_MODEL", "")
    respx.post(GEMINI_TEST_URL).mock(return_value=httpx.Response(500, text="Internal error"))
    fallback = respx.post(GEMINI_FALLBACK_URL).mock(return_value=httpx.Response(200, json={}))
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    assert "trouble reading that" in r.json()["text"].lower()
    assert not fallback.called


# --------------------------------------------------------------------------
# /read_document -- unreadable / empty model output
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model_text",
    ["UNREADABLE", "unreadable", "  UNREADABLE  ", "UNREADABLE\n", "UNREADABLE - too dark"],
)
@respx.mock
def test_read_document_unreadable_returns_hold_it_closer(client, image_file, model_text):
    respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(200, json=text_payload(model_text))
    )
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    body = r.json()
    assert "closer" in body["text"].lower()
    assert "flatten" in body["text"].lower()
    assert "UNREADABLE" not in body["text"].upper()
    assert "elapsed_s" in body


@pytest.mark.parametrize(
    "payload",
    [
        text_payload(""),
        text_payload("   \n  "),
        gemini_payload(),
        {"candidates": []},
        {},
        {"candidates": [{}]},
        {"candidates": [{"content": {}}]},
        {"candidates": [{"content": {"parts": None}}]},
        {"candidates": None},
        {"promptFeedback": {"blockReason": "SAFETY"}},
    ],
    ids=[
        "empty-text",
        "whitespace-text",
        "no-parts",
        "empty-candidates",
        "bare-object",
        "candidate-without-content",
        "content-without-parts",
        "null-parts",
        "null-candidates",
        "blocked-prompt-feedback",
    ],
)
@respx.mock
def test_read_document_empty_or_malformed_payload_does_not_raise(client, image_file, payload):
    """Malformed upstream JSON must degrade to the retry line, never a traceback."""
    respx.post(GEMINI_TEST_URL).mock(return_value=httpx.Response(200, json=payload))
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 200
    assert "closer" in r.json()["text"].lower()


# --------------------------------------------------------------------------
# /read_document -- request-side validation
# --------------------------------------------------------------------------


def test_read_document_empty_upload_is_400(client):
    r = client.post("/read_document", files={"image": ("frame.jpg", b"", "image/jpeg")})
    assert r.status_code == 400
    assert "empty image upload" in r.json()["detail"]


def test_read_document_missing_gemini_key_is_500(client, appmod, monkeypatch, image_file):
    monkeypatch.setattr(appmod, "GEMINI_API_KEY", "")
    r = client.post("/read_document", files=image_file)
    assert r.status_code == 500
    assert "GEMINI_API_KEY is not set" in r.json()["detail"]


def test_read_document_missing_key_is_checked_before_reading_the_body(client, appmod, monkeypatch):
    """No key means no work: an empty upload still 500s on the key, not 400s."""
    monkeypatch.setattr(appmod, "GEMINI_API_KEY", "")
    r = client.post("/read_document", files={"image": ("frame.jpg", b"", "image/jpeg")})
    assert r.status_code == 500


def test_read_document_wrong_form_field_name_is_422(client, jpeg_bytes):
    """The client tool in App.tsx must send the field as "image"."""
    r = client.post("/read_document", files={"file": ("frame.jpg", jpeg_bytes, "image/jpeg")})
    assert r.status_code == 422


def test_read_document_no_file_at_all_is_422(client):
    assert client.post("/read_document").status_code == 422


@respx.mock
def test_read_document_falls_back_to_jpeg_mime_when_unset(client, jpeg_bytes):
    """UploadFile.content_type can be absent; app.py defaults it to image/jpeg."""
    route = respx.post(GEMINI_TEST_URL).mock(
        return_value=httpx.Response(200, json=text_payload("FROM: Someone"))
    )
    r = client.post("/read_document", files={"image": ("frame.jpg", jpeg_bytes, None)})
    assert r.status_code == 200
    sent = json.loads(route.calls.last.request.content)
    assert sent["contents"][0]["parts"][1]["inline_data"]["mime_type"]


# --------------------------------------------------------------------------
# No test in this file may touch the network.
# --------------------------------------------------------------------------


@respx.mock(assert_all_called=False)
def test_suite_is_offline_unmocked_calls_are_refused(client, image_file):
    """Sanity check: with no route registered, an outbound call must blow up.

    This is what proves the rest of the file is mocked rather than lucky.
    """
    with pytest.raises(Exception):
        client.post("/read_document", files=image_file)
