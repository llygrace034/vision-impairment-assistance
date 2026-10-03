# scripts/

Operator scripts for LetterLens. Run them with the repo-root venv:
`.venv\Scripts\python.exe scripts\<name>.py`.

## `configure_agent.py`

Pushes the persona and the `read_document` tool onto the live ElevenLabs agent.
**A human runs this once**, because creating a tool and patching the agent are
writes to a shared workspace resource.

```powershell
.venv\Scripts\python.exe scripts\configure_agent.py --verify    # read-only: what is live now
.venv\Scripts\python.exe scripts\configure_agent.py --dry-run   # read-only: the exact bodies it would send
.venv\Scripts\python.exe scripts\configure_agent.py             # apply, then verify
```

Resolves the repo root from `__file__`, so it works from any cwd (unlike
`backend/app.py`, which must be started from the repo root). Requires
`ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID` in `.env.local`; exits 2 naming
the missing one. Exits 1 on any API failure, printing the HTTP status and the
first 300 characters of the body. Never prints the key.

What it writes:

| Target | Change | Why |
| --- | --- | --- |
| `/v1/convai/tools` | create or patch the tool named `read_document` from `agent/tools/read_document.json`, forcing `tool_error_handling_mode: "summarized"` | The default `auto` **hides** a failed frame read from the model, which then invents an appointment instead of asking the user to hold the letter closer. The field lives on the tool, not on the agent. |
| `conversation_config.agent.prompt.prompt` / `.first_message` | parsed out of the fenced blocks in `agent/persona-prompt.md` | That markdown is the single source of truth; the prompt text is deliberately not duplicated in the script. |
| `conversation_config.agent.prompt.tool_ids` | `[<id of read_document>]` | `prompt.tools` is deprecated — an inline tool list is accepted and then does nothing. |
| `conversation_config.conversation.client_events` | existing list **plus** `interruption` | Without it barge-in fails silently: the user talks over the agent and is simply not heard. The script GETs the agent first and merges, because a PATCH replaces the whole list. |
| `conversation_config.conversation.text_only` | `false` | A `text_only` agent emits no audio at all, which on stage is indistinguishable from a dead microphone. |

Idempotent: re-running patches the existing tool rather than creating a second
one with the same name.
