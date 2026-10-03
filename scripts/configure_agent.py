"""Push LetterLens' persona and its `read_document` tool onto the live ElevenLabs agent.

Run once, by a human, from anywhere:

    .venv\\Scripts\\python.exe scripts\\configure_agent.py

A freshly created ElevenLabs agent is a factory shell: the system prompt is the
placeholder "Hello! How can I help you today?", `tool_ids` is empty and no
persona exists, so the agent will never call `read_document` and LetterLens has
no product. This script is the one write that turns that shell into the demo.

Three read-only modes exist so nobody has to guess what it will do:

    --dry-run   every GET, then print the exact JSON bodies it WOULD send
    --verify    GET only, print the verification block (safe to run any time)
    (no flag)   do the writes, then verify

Sources for the API shapes used here: docs/research/05-elevenlabs-agent-creation.md
sections 4-5 and docs/research/03-elevenlabs-server-tools-and-variables.md
sections 1 and 5. The prompt text itself is NOT duplicated in this file -- it is
parsed out of agent/persona-prompt.md, which is the single source of truth. A
copy pasted here would drift from the markdown within a day.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Resolve the repo root from this file, not from the cwd. backend/app.py calls
# load_dotenv(".env.local") with a relative path and therefore only works when
# started from the repo root -- a trap this script must not repeat, because the
# operator will run it from wherever their terminal happens to sit and an empty
# ELEVENLABS_API_KEY would otherwise look like a 401 from the API.
REPO_ROOT = Path(__file__).resolve().parents[1]

PERSONA_PATH = REPO_ROOT / "agent" / "persona-prompt.md"
TOOL_PATH = REPO_ROOT / "agent" / "tools" / "read_document.json"

API_BASE = "https://api.elevenlabs.io"
TOOL_NAME = "read_document"
TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# Barge-in is the whole accessibility story: a blind user must be able to talk
# over a summary and be heard. If "interruption" is missing from client_events
# the SDK is never told to stop playback, so the user talks and is simply
# ignored -- no error, no log line, nothing to debug. Keep it in the list.
REQUIRED_CLIENT_EVENT = "interruption"

# Default is "auto", which for a non-native tool means *hide*: a failed frame
# read reaches the model as nothing at all and it invents an appointment rather
# than admitting it could not read the letter. "summarized" hands the model
# speakable text instead. (research 03 section 1.3 / 7.3.)
TOOL_ERROR_MODE = "summarized"


class Failure(Exception):
    """Anything that should end the run with a non-zero exit and a clear reason."""


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


def parse_fenced_block(markdown: str, heading: str) -> str:
    """Return the first fenced block under `heading` in `markdown`.

    The fence language is accepted loosely (```text, ```, ```md) because the
    markdown is hand-edited and a missing language tag should not break the
    deploy; the *heading* is what identifies the block.
    """
    # Stop at the next heading of the same or higher level so a block further
    # down the file can never be picked up when the expected one is absent.
    section = re.search(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^#{{1,2}}\s|\Z)",
        markdown,
        re.MULTILINE | re.DOTALL,
    )
    if not section:
        raise Failure(f"{PERSONA_PATH}: no '## {heading}' heading found")

    block = re.search(r"^```[a-zA-Z]*\n(.*?)^```", section.group(1), re.MULTILINE | re.DOTALL)
    if not block:
        raise Failure(f"{PERSONA_PATH}: '## {heading}' has no fenced block")

    text = block.group(1).strip()
    if not text:
        raise Failure(f"{PERSONA_PATH}: the fenced block under '## {heading}' is empty")
    return text


def load_persona() -> tuple[str, str]:
    if not PERSONA_PATH.is_file():
        raise Failure(f"missing {PERSONA_PATH}")
    markdown = PERSONA_PATH.read_text(encoding="utf-8")
    return (
        parse_fenced_block(markdown, "System prompt"),
        parse_fenced_block(markdown, "First message"),
    )


def load_tool_config() -> dict[str, Any]:
    """Read the tool body, unwrapping the REST envelope if the file has one.

    The CLI writes tool configs unwrapped (`type`/`name`/... at top level) while
    POST /v1/convai/tools wants them nested under `tool_config`. Both spellings
    are in circulation in this repo's own docs, so accept either.
    """
    if not TOOL_PATH.is_file():
        raise Failure(f"missing {TOOL_PATH}")
    try:
        raw = json.loads(TOOL_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Failure(f"{TOOL_PATH}: invalid JSON -- {exc}") from exc

    config = raw.get("tool_config", raw)
    if not isinstance(config, dict) or "name" not in config:
        raise Failure(f"{TOOL_PATH}: expected a tool config object with a 'name'")
    if config["name"] != TOOL_NAME:
        raise Failure(f"{TOOL_PATH}: tool is named {config['name']!r}, expected {TOOL_NAME!r}")

    # Set on the *tool*, not on the agent: tool_error_handling_mode is a field of
    # the tool config in the API schema, and the agent body has no equivalent.
    config["tool_error_handling_mode"] = TOOL_ERROR_MODE
    return config


def require_env() -> tuple[str, str]:
    # .env.local holds the real keys and must win over any committed .env.
    load_dotenv(REPO_ROOT / ".env.local")
    load_dotenv(REPO_ROOT / ".env")

    missing = [n for n in ("ELEVENLABS_API_KEY", "ELEVENLABS_AGENT_ID") if not os.getenv(n)]
    if missing:
        print(
            f"error: {', '.join(missing)} not set.\n"
            f"       Add it to {REPO_ROOT / '.env.local'} and re-run.",
            file=sys.stderr,
        )
        sys.exit(2)
    return os.environ["ELEVENLABS_API_KEY"], os.environ["ELEVENLABS_AGENT_ID"]


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #


def request(client: httpx.Client, method: str, path: str, body: Any = None) -> Any:
    try:
        response = client.request(method, path, json=body)
    except httpx.HTTPError as exc:
        raise Failure(f"{method} {path} failed: {exc!r}") from exc
    if response.status_code >= 400:
        # The first 300 characters of an ElevenLabs error body carry the 422
        # `detail[].loc` path, which is the only thing that tells you which
        # field of a deeply nested conversation_config it rejected.
        raise Failure(f"{method} {path} -> HTTP {response.status_code}: {response.text[:300]}")
    return response.json() if response.content else {}


def find_tool_id(client: httpx.Client) -> str | None:
    """Return the workspace tool id named `read_document`, or None.

    Creating a second tool with the same name is legal and silently halves the
    chance the agent calls the right one, so this list-then-decide step is what
    makes the script safe to re-run.
    """
    cursor: str | None = None
    while True:
        path = "/v1/convai/tools" + (f"?cursor={cursor}" if cursor else "")
        page = request(client, "GET", path)
        for tool in page.get("tools", []):
            if (tool.get("tool_config") or {}).get("name") == TOOL_NAME:
                return tool["id"]
        if not page.get("has_more"):
            return None
        cursor = page.get("next_cursor")
        if not cursor:
            return None


def agent_patch_body(prompt: str, first_message: str, tool_id: str, agent: dict) -> dict:
    conversation = agent.get("conversation_config", {}).get("conversation", {})

    # Merge, never clobber: the live agent already carries client_events the
    # frontend depends on (user_transcript, agent_response, ...) and a PATCH
    # replaces the whole list. Sending only ["interruption"] would mute the UI.
    events = list(conversation.get("client_events") or [])
    if REQUIRED_CLIENT_EVENT not in events:
        events.append(REQUIRED_CLIENT_EVENT)

    return {
        "conversation_config": {
            "agent": {
                "first_message": first_message,
                "prompt": {
                    "prompt": prompt,
                    # tool_ids, not prompt.tools: the inline `tools` list is
                    # deprecated and accepting it is not the same as using it --
                    # the agent takes the write and still calls nothing.
                    "tool_ids": [tool_id],
                },
            },
            "conversation": {
                "client_events": events,
                # A text_only agent produces no audio at all. The dashboard
                # leaves this on for agents created through the API, which for a
                # voice demo looks exactly like a broken microphone.
                "text_only": False,
            },
        }
    }


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #


def print_verification(client: httpx.Client, agent_id: str) -> None:
    agent = request(client, "GET", f"/v1/convai/agents/{agent_id}")
    conversation_config = agent.get("conversation_config", {})
    agent_cfg = conversation_config.get("agent", {})
    prompt_cfg = agent_cfg.get("prompt", {})
    conversation = conversation_config.get("conversation", {})

    prompt = prompt_cfg.get("prompt") or ""
    tool_ids = prompt_cfg.get("tool_ids") or []
    events = conversation.get("client_events") or []

    print("--- verification ---")
    print(f"agent_id          : {agent_id}")
    print(f"name              : {agent.get('name')}")
    print(f"prompt length     : {len(prompt)} chars")
    print(f"prompt first 60   : {prompt[:60]!r}")
    print(f"first_message     : {agent_cfg.get('first_message')!r}")
    print(f"tool_ids          : {tool_ids}")
    print(f"client_events     : {events}")
    print(f"  interruption?   : {'yes' if REQUIRED_CLIENT_EVENT in events else 'NO -- barge-in will fail silently'}")
    print(f"text_only         : {conversation.get('text_only')}"
          f"{'  <-- NO AUDIO, the agent cannot speak' if conversation.get('text_only') else ''}")

    # The error-handling mode lives on the tool, so read it back per tool id
    # rather than claiming anything about it from the agent body.
    for tool_id in tool_ids:
        tool_config = request(client, "GET", f"/v1/convai/tools/{tool_id}").get("tool_config", {})
        print(
            f"tool {tool_id}: name={tool_config.get('name')!r} "
            f"type={tool_config.get('type')!r} "
            f"expects_response={tool_config.get('expects_response')} "
            f"tool_error_handling_mode={tool_config.get('tool_error_handling_mode')!r}"
        )
    if not tool_ids:
        print("tool error mode   : n/a -- no tools attached, read_document can never fire")
    print("--- end ---")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="GET only; print the bodies it would send")
    mode.add_argument("--verify", action="store_true", help="GET only; print the verification block")
    args = parser.parse_args()

    api_key, agent_id = require_env()
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    with httpx.Client(base_url=API_BASE, headers=headers, timeout=TIMEOUT) as client:
        if args.verify:
            print_verification(client, agent_id)
            return 0

        prompt, first_message = load_persona()
        tool_config = load_tool_config()
        print(f"parsed prompt ({len(prompt)} chars) and first message from {PERSONA_PATH.name}")

        existing_tool_id = find_tool_id(client)
        agent = request(client, "GET", f"/v1/convai/agents/{agent_id}")

        if args.dry_run:
            if existing_tool_id:
                print(f"\nWOULD PATCH /v1/convai/tools/{existing_tool_id}")
            else:
                print("\nWOULD POST /v1/convai/tools   (no tool named read_document exists yet)")
            print(json.dumps({"tool_config": tool_config}, indent=2))

            placeholder = existing_tool_id or "<id returned by the create call>"
            print(f"\nWOULD PATCH /v1/convai/agents/{agent_id}")
            print(json.dumps(agent_patch_body(prompt, first_message, placeholder, agent), indent=2))
            print("\nno write calls were made. Re-run without --dry-run to apply.\n")
            print_verification(client, agent_id)
            return 0

        if existing_tool_id:
            tool = request(
                client, "PATCH", f"/v1/convai/tools/{existing_tool_id}", {"tool_config": tool_config}
            )
            print(f"patched tool {existing_tool_id}")
        else:
            tool = request(client, "POST", "/v1/convai/tools", {"tool_config": tool_config})
            print(f"created tool {tool.get('id')}")
        tool_id = tool.get("id") or existing_tool_id
        if not tool_id:
            raise Failure("the tools endpoint returned no id; agent not patched")

        request(
            client,
            "PATCH",
            f"/v1/convai/agents/{agent_id}",
            agent_patch_body(prompt, first_message, tool_id, agent),
        )
        print(f"patched agent {agent_id}\n")
        print_verification(client, agent_id)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Failure as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
