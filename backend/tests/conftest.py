"""Offline test harness for backend/app.py.

Two things have to be true before `app` is imported:

1. No test may depend on .env.local. app.py calls `load_dotenv(".env.local")`
   at import time with a *relative* path, so whether real keys land in
   os.environ depends on the cwd pytest happened to be started from. Setting
   placeholder values here first makes that irrelevant: python-dotenv does not
   override an existing environment variable, so these win either way and the
   suite behaves identically with or without .env.local on disk.
2. `backend/` is not a package, so it has to go on sys.path by hand.

Every test then monkeypatches the module-level globals it cares about, because
app.py reads them through module scope at request time rather than capturing
them in a closure.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Must happen before `import app` runs load_dotenv(). Placeholders only -- any
# test that exercises a key path sets the value it needs explicitly.
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-elevenlabs-key")
os.environ.setdefault("ELEVENLABS_AGENT_ID", "test-agent-id")
os.environ.setdefault("GEMMA_VISION_MODEL", "gemma-4-26b-a4b-it")

import app as app_module  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

GEMINI_TEST_MODEL = "gemma-test-model"
GEMINI_TEST_URL = app_module.GEMINI_URL.format(model=GEMINI_TEST_MODEL)
GEMINI_FALLBACK_MODEL = "fallback-test-model"
GEMINI_FALLBACK_URL = app_module.GEMINI_URL.format(model=GEMINI_FALLBACK_MODEL)
ELEVENLABS_TOKEN_URL = "https://api.elevenlabs.io/v1/convai/conversation/token"


@pytest.fixture
def appmod():
    """The imported app module, for monkeypatching its globals."""
    return app_module


@pytest.fixture
def client():
    with TestClient(app_module.app) as c:
        yield c


@pytest.fixture(autouse=True)
def pinned_config(monkeypatch):
    """Pin every config global so no test reads the developer's real .env.local."""
    monkeypatch.setattr(app_module, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(app_module, "VISION_MODEL", GEMINI_TEST_MODEL)
    monkeypatch.setattr(app_module, "VISION_FALLBACK_MODEL", GEMINI_FALLBACK_MODEL)
    monkeypatch.setattr(app_module, "ELEVENLABS_API_KEY", "test-elevenlabs-key")
    monkeypatch.setattr(app_module, "ELEVENLABS_AGENT_ID", "test-agent-id")


@pytest.fixture(scope="session")
def jpeg_bytes() -> bytes:
    """A real, tiny JPEG generated in memory -- no binary fixture in the repo."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (240, 240, 235)).save(buf, format="JPEG", quality=75)
    return buf.getvalue()


@pytest.fixture
def image_file(jpeg_bytes):
    """The multipart payload. The form field name must be exactly "image"."""
    return {"image": ("frame.jpg", jpeg_bytes, "image/jpeg")}


def gemini_payload(*parts: dict) -> dict:
    """A generateContent response body with the given parts."""
    return {"candidates": [{"content": {"parts": list(parts)}}]}


def text_payload(text: str) -> dict:
    return gemini_payload({"text": text})
