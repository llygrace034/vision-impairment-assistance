#!/usr/bin/env python
"""LetterLens demo preflight -- read-only.

Checks the four things that must all be true at once before the demo can work:
secrets loaded, deps installed, backend answering from the *right* working
directory, and the live ElevenLabs agent actually configured.

The failure this file exists to catch: backend/app.py calls
load_dotenv(".env.local") with a RELATIVE path. Start uvicorn from inside
backend/ and the server boots happily, answers /health with every key false,
and then fails mid-demo, out loud. /health is therefore checked for its key
booleans, not just for a 200.

Output is deliberately plain ASCII ([ok] / [MISSING] / [warn]) -- this gets run
while screen-sharing and read aloud in a hurry, and a Windows console mangles
emoji and colour. No secret value is ever printed, not even partially.

Run:  .venv\\Scripts\\python.exe scripts\\preflight.py
Exit: 0 = ready, 1 = something required is missing.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import httpx
except ImportError:  # pragma: no cover - reported as a failure below instead
    httpx = None  # type: ignore[assignment]

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover
    dotenv_values = None  # type: ignore[assignment]

# Resolve the repo root from this file, never from cwd: the whole point of this
# script is that it must behave identically no matter where it is invoked from.
ROOT = Path(__file__).resolve().parent.parent

REQUIRED_KEYS = (
    "GEMINI_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_AGENT_ID",
    "GEMMA_VISION_MODEL",
)
REQUIRED_IMPORTS = ("fastapi", "httpx", "uvicorn", "dotenv")
TEST_LETTERS = (
    "01-hospital-appointment.png",
    "02-parking-penalty.png",
    "03-school-trip-consent.png",
)
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
VENV_PYTHON_POSIX = ROOT / ".venv" / "bin" / "python"

# Minimum prompt length that distinguishes a configured agent from a factory
# default one. A fresh ElevenLabs agent ships with a one-line placeholder.
MIN_PROMPT_CHARS = 200

_failures: list[str] = []
_warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"  [ok]      {msg}")


def missing(msg: str, fix: str = "") -> None:
    print(f"  [MISSING] {msg}")
    if fix:
        print(f"            fix: {fix}")
    _failures.append(msg)


def warn(msg: str, fix: str = "") -> None:
    print(f"  [warn]    {msg}")
    if fix:
        print(f"            fix: {fix}")
    _warnings.append(msg)


def info(msg: str) -> None:
    print(f"            {msg}")


def section(title: str) -> None:
    print()
    print(f"== {title}")


def load_env() -> dict[str, str]:
    """Read .env.local into a dict. Values are never printed, only tested."""
    env_path = ROOT / ".env.local"
    section("1. secrets (.env.local)")
    if not env_path.is_file():
        missing(
            ".env.local not found at the repo root",
            "copy .env.example to .env.local and fill in the real keys",
        )
        return {}
    if dotenv_values is None:
        missing(
            "python-dotenv is not importable, cannot parse .env.local",
            f'"{VENV_PYTHON}" scripts\\preflight.py',
        )
        return {}

    raw = dotenv_values(env_path)
    values = {k: (v or "") for k, v in raw.items()}
    ok(f".env.local found ({env_path})")
    for key in REQUIRED_KEYS:
        if values.get(key, "").strip():
            ok(f"{key} SET")
        else:
            missing(f"{key} MISSING or empty in .env.local")
    return values


def check_frontend() -> None:
    section("2. frontend deps")
    node_modules = ROOT / "frontend" / "node_modules"
    if node_modules.is_dir():
        ok("frontend/node_modules present")
    else:
        missing(
            "frontend/node_modules is absent",
            "cd frontend; npm install",
        )


def check_python_env() -> None:
    section("3. python env (.venv)")
    interpreter = VENV_PYTHON if VENV_PYTHON.is_file() else VENV_PYTHON_POSIX
    if not interpreter.is_file():
        missing(
            f"no .venv interpreter at {VENV_PYTHON}",
            "python -m venv .venv; .venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt",
        )
        return
    ok(f".venv interpreter present ({interpreter})")

    probe = ";".join(f"import {m}" for m in REQUIRED_IMPORTS)
    try:
        proc = subprocess.run(
            [str(interpreter), "-c", probe],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        missing(f"could not run the .venv interpreter: {exc.__class__.__name__}")
        return

    if proc.returncode == 0:
        ok("imports fastapi, httpx, uvicorn, dotenv -- all available")
    else:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = tail[-1] if tail else f"exit {proc.returncode}"
        missing(
            f"backend imports failed in .venv ({detail})",
            '"%s" -m pip install -r backend\\requirements.txt' % interpreter,
        )


def check_test_letters() -> None:
    section("4. test letters")
    folder = ROOT / "test-letters"
    if not folder.is_dir():
        missing(
            "test-letters/ not found",
            "the three demo PNGs live there; regenerate with test-letters\\generate.py",
        )
        return
    for name in TEST_LETTERS:
        if (folder / name).is_file():
            ok(f"test-letters/{name}")
        else:
            missing(f"test-letters/{name} is absent")


def backend_port(env: dict[str, str], args: argparse.Namespace) -> tuple[str, str]:
    """Explicit flag > .env.local > process env > default."""
    host = (args.host or env.get("HOST") or os.getenv("HOST") or "127.0.0.1").strip()
    port = (args.port or env.get("PORT") or os.getenv("PORT") or "8000").strip()
    if host in ("0.0.0.0", ""):
        host = "127.0.0.1"
    return host, port


def check_backend(env: dict[str, str], args: argparse.Namespace) -> None:
    host, port = backend_port(env, args)
    base = f"http://{host}:{port}"
    section(f"5. backend ({base})")

    if httpx is None:
        missing("httpx is not importable, cannot probe the backend")
        return

    try:
        r = httpx.get(f"{base}/health", timeout=4.0)
    except Exception:
        warn(
            f"backend is not answering on {base} yet (that is fine before launch)",
            "scripts\\dev.ps1 starts it, or: "
            f'.venv\\Scripts\\python.exe -m uvicorn backend.app:app --host {host} --port {port} '
            "  <-- run this FROM THE REPO ROOT",
        )
        return

    if r.status_code != 200:
        missing(f"GET {base}/health returned {r.status_code}, expected 200")
        return

    try:
        data = r.json()
    except ValueError:
        missing(f"GET {base}/health did not return JSON")
        return

    ok(f"GET /health -> 200 (vision_model: {data.get('vision_model')})")

    gemini = bool(data.get("gemini_key"))
    eleven = bool(data.get("elevenlabs_key"))
    agent = bool(data.get("agent_id"))

    if gemini and eleven and agent:
        ok("/health reports gemini_key, elevenlabs_key and agent_id all loaded")
        return

    # THE high-value message in this script.
    missing(
        "the running backend has NO KEYS LOADED -- it was started from the wrong "
        "working directory",
        "kill it and restart uvicorn with the REPO ROOT as the current directory: "
        "backend/app.py calls load_dotenv('.env.local') with a relative path, so "
        "starting from inside backend/ loads every key empty and the server still "
        "answers 200.",
    )
    info(
        "gemini_key=%s  elevenlabs_key=%s  agent_id=%s"
        % (gemini, eleven, agent)
    )
    info("correct command, from C:\\Users\\arun\\vision-impairment-assistance :")
    info(
        f"  .venv\\Scripts\\python.exe -m uvicorn backend.app:app --host {host} --port {port}"
    )
    info("or just: powershell -ExecutionPolicy Bypass -File scripts\\dev.ps1")


def check_agent(env: dict[str, str]) -> None:
    section("6. live ElevenLabs agent (read-only GET)")
    api_key = (env.get("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY") or "").strip()
    agent_id = (env.get("ELEVENLABS_AGENT_ID") or os.getenv("ELEVENLABS_AGENT_ID") or "").strip()

    if not (api_key and agent_id):
        warn("skipped: ELEVENLABS_API_KEY or ELEVENLABS_AGENT_ID is not set")
        return
    if httpx is None:
        warn("skipped: httpx is not importable")
        return

    try:
        r = httpx.get(
            f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}",
            headers={"xi-api-key": api_key},
            timeout=15.0,
        )
    except Exception as exc:
        warn(f"could not reach the ElevenLabs API ({exc.__class__.__name__})")
        return

    if r.status_code != 200:
        warn(
            f"GET /v1/convai/agents/<id> returned {r.status_code}",
            "check ELEVENLABS_AGENT_ID and that the key owns that agent",
        )
        return

    try:
        data = r.json()
    except ValueError:
        warn("agent lookup did not return JSON")
        return

    ok(f"agent reachable (name: {data.get('name')!r})")

    agent_cfg = ((data.get("conversation_config") or {}).get("agent")) or {}
    prompt_cfg = agent_cfg.get("prompt") or {}
    prompt = prompt_cfg.get("prompt") or ""
    tool_ids = prompt_cfg.get("tool_ids") or []

    if len(prompt) >= MIN_PROMPT_CHARS:
        ok(f"system prompt configured ({len(prompt)} chars)")
    else:
        warn(
            f"system prompt is only {len(prompt)} chars -- this agent looks "
            "factory-default",
            "run scripts\\configure_agent.py once to push the LetterLens persona",
        )

    if tool_ids:
        ok(f"tool_ids attached ({len(tool_ids)})")
    else:
        warn(
            "tool_ids is empty -- the agent has no read_document client tool, so "
            "it will never call the backend",
            "run scripts\\configure_agent.py once to register read_document",
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LetterLens demo preflight (read-only).",
    )
    parser.add_argument(
        "--host",
        default="",
        help="backend host to probe (default: HOST from .env.local, else 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        default="",
        help="backend port to probe (default: PORT from .env.local, else 8000)",
    )
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="skip the live ElevenLabs agent lookup (offline runs)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print("LetterLens preflight")
    print(f"repo root: {ROOT}")
    print("(read-only; no secret values are printed)")

    env = load_env()
    check_frontend()
    check_python_env()
    check_test_letters()
    check_backend(env, args)
    if args.skip_agent:
        section("6. live ElevenLabs agent (read-only GET)")
        print("  [skip]    --skip-agent was passed")
    else:
        check_agent(env)

    print()
    print("=" * 62)
    if _failures:
        print(f"RESULT: NOT READY -- {len(_failures)} required check(s) failed")
        for f in _failures:
            print(f"  - {f}")
        if _warnings:
            print(f"  ({len(_warnings)} warning(s) too)")
        print("=" * 62)
        return 1

    if _warnings:
        print(f"RESULT: READY, with {len(_warnings)} warning(s)")
        for w in _warnings:
            print(f"  - {w}")
    else:
        print("RESULT: READY -- all checks passed")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
