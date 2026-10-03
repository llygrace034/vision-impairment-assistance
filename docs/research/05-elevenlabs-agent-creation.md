# 05 — Creating / configuring an ElevenLabs Agent programmatically (CLI + REST)

**Research date:** 2026-10-03
**Dimension:** Agents-as-code CLI and REST API for creating/configuring an ElevenLabs Agent.
**Method:** every fact below was pulled from a page fetched during this research pass. Sources are listed per section. Where a doc page did not confirm something, it says so explicitly.

Primary sources used (all fetched 2026-10-03):

| # | Source | URL |
|---|---|---|
| S1 | ElevenLabs CLI docs | https://elevenlabs.io/docs/eleven-agents/operate/cli.md |
| S2 | Agents Quickstart | https://elevenlabs.io/docs/eleven-agents/quickstart.md |
| S3 | API ref — Create agent | https://elevenlabs.io/docs/api-reference/agents/create.md (HTML: https://elevenlabs.io/docs/api-reference/agents/create) |
| S4 | API ref — Create tool | https://elevenlabs.io/docs/api-reference/tools/create.md |
| S5 | Models (native LLM list) | https://elevenlabs.io/docs/eleven-agents/customization/llm.md |
| S6 | Integrate your own model (custom LLM) | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm.md |
| S7 | Tools overview | https://elevenlabs.io/docs/eleven-agents/customization/tools.md |
| S8 | Webhook tools | https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md |
| S9 | Client tools | https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools.md |
| S10 | API authentication | https://elevenlabs.io/docs/api-reference/authentication.md |
| S11 | CLI source of truth (README) | https://raw.githubusercontent.com/elevenlabs/cli/main/README.md |
| S12 | CLI templates source | https://raw.githubusercontent.com/elevenlabs/cli/main/cli/elevenlabs/workflow/templates.rs |
| S13 | CLI project/registry source | https://raw.githubusercontent.com/elevenlabs/cli/main/cli/elevenlabs/workflow/project.rs |
| S14 | OpenAPI spec (live) | https://api.elevenlabs.io/openapi.json |
| S15 | React SDK | https://elevenlabs.io/docs/eleven-agents/libraries/react.md |
| S16 | Agents pricing page | https://elevenlabs.io/pricing/agents |
| S17 | Burst pricing | https://elevenlabs.io/docs/eleven-agents/guides/burst-pricing.md |
| S18 | Agents cost (help center) | https://elevenlabs.io/docs/help-center/product/eleven-agents/how-much-does-eleven-agents-cost.md |
| S19 | Call queueing | https://elevenlabs.io/docs/eleven-agents/guides/call-queueing.md |

> Terminology note: the product is called **"ElevenAgents" / "ElevenLabs Agents"** in current docs; the API path is still `/v1/convai/...` and the SDK namespace is still `conversational_ai` / `conversationalAi`. Both names appear across docs (S2, S3).

---

## 1. The four creation paths (S2)

The quickstart lists four ways to create an agent:

1. **Web dashboard** — https://elevenlabs.io/app/agents
2. **CLI** — install via Homebrew, Scoop, npm or curl, then `elevenlabs agents init` and `elevenlabs agents push`
3. **API / SDK** — Python and TypeScript SDKs create agents programmatically
4. **MCP server** — a "hosted MCP server" at `/docs/eleven-agents/operate/hosted-mcp` that allows "managing agents through natural language"

For LetterLens the two relevant ones are the CLI (agents in git) and the REST API (create at runtime / in a setup script).

---

## 2. The CLI ("agents as code")

### 2.1 Package name and install commands (S1, S11)

**npm package: `@elevenlabs/cli`. Installed binary name: `elevenlabs`.**

Verbatim from S1:

```bash title="Homebrew (macOS)"
brew install elevenlabs/tap/elevenlabs
```

```powershell title="Scoop (Windows)"
scoop bucket add elevenlabs https://github.com/elevenlabs/scoop-bucket
scoop install elevenlabs
```

```bash title="npm"
npm install -g @elevenlabs/cli
```

```bash title="curl"
curl --proto '=https' --tlsv1.2 -LsSf https://github.com/elevenlabs/cli/releases/latest/download/elevenlabs-cli-installer.sh | sh
```

S1 verbatim: "Homebrew (macOS) and Scoop (Windows) are the recommended install methods and ship a standalone binary." and "After installation, the `elevenlabs` command will be available globally in your terminal."

S11 on the npm route, verbatim: "Installs the same binary through a thin launcher, picking the right build for your platform. Use `npx @elevenlabs/cli <command>` to run it once without installing it globally."

**Confirmed version:** `https://registry.npmjs.org/@elevenlabs/cli/latest` returned `@elevenlabs/cli 1.4.0`, description "CLI for elevenlabs", bin `{"elevenlabs": "bin/cli.js"}` (fetched 2026-10-03). On Windows (the LetterLens dev box) either `scoop install elevenlabs` or `npm i -g @elevenlabs/cli` works; `npx @elevenlabs/cli <command>` avoids a global install.

> **v0 → v1 breaking change (S11, verbatim):** "**Migrating from v0 (`@elevenlabs/cli`):** v0's `agents list` showed local config and `agents delete <id>` took a positional and cleaned up locally. In v1 both names belong to the API surface — use `agents status` for the local view, and `--agent-id` for delete. v0's `agents widget <id>` is now `agents widget embed <id>`, since `agents widget` is an API subgroup."

### 2.2 Highest-leverage extra command (S1, verbatim)

"Working with an AI coding assistant? Run `elevenlabs generate-skills` in your project to write a `SKILL.md` for every command group into `skills/`, so your assistant knows the CLI's full surface without you pasting docs. Use `--output-dir` to put them elsewhere. This reads the CLI's own embedded API definition, so it needs no API key and works offline — and it stays in step with whichever CLI version you have installed."

Run this once and the repo gets authoritative, version-matched CLI docs offline.

### 2.3 Authentication (S1)

```bash title="Login"
elevenlabs auth login
```
```bash title="Logout"
elevenlabs auth logout
```

Verbatim: "`elevenlabs auth login` stores credentials in your operating system's keyring — Keychain on macOS, Credential Manager on Windows, and the Secret Service on Linux. Where no keyring is available, the CLI falls back to `~/.config/elevenlabs/auth-keyring.json` with `0600` permissions. Run `elevenlabs auth status` to see which source is in use, and `elevenlabs auth logout` to remove the stored entry."

Verbatim: "For CI, set `ELEVENLABS_API_KEY` in the environment or a `.env` file instead of logging in."

### 2.4 Commands — full surface (S11, verbatim)

```bash
# Scaffold a new project (pass a path, or --override to reset an existing one)
elevenlabs agents init [path] [--override]

# Create an agent from a template (or an existing file), upload it, and register it
elevenlabs agents add <name> [--template <template>] [--output-path <path>]
elevenlabs agents add [name] --from-file <path>

# Show the status of locally-configured agents
elevenlabs agents status

# Sync configs with ElevenLabs (push force-overrides main + registered branches)
elevenlabs agents push [--agent <agent_id>] [--branch <name|id>] [--version-description <text>] [--dry-run]
elevenlabs agents pull [--agent <agent_id>] [--branch <name|id>] [--all-branches] [--update] [--all] [--dry-run]

# List available agent templates, or print one's full configuration
elevenlabs agents templates list
elevenlabs agents templates show <template>

# Print an embeddable HTML widget snippet for an agent
elevenlabs agents widget embed <agent_id>

# Run the tests attached to an agent (polls to completion; exits non-zero on failure)
elevenlabs agents test <agent_id>
```

Tools (S11, verbatim):

```bash
# Create a webhook or client tool, upload it, and register it in tools.json
elevenlabs tools add <name> [--type webhook|client] [--config-path <path>]

# Sync tool configs with ElevenLabs
elevenlabs tools push [--tool <tool_id>] [--dry-run]
elevenlabs tools pull [--tool <tool_id>] [--output-dir tool_configs] [--update] [--all] [--dry-run]

# Delete a tool locally and in ElevenLabs
elevenlabs tools delete <tool_id>
elevenlabs tools delete --all
```

**There is NO `sync` command and NO `watch` command.** The verbs are `init`, `add`, `status`, `push`, `pull`, `templates`, `widget embed`, `test`. Synchronisation is `push` / `pull`. (Confirmed by grepping S11 and S1 for "watch" and "sync" — only `push`/`pull` appear. Confidence: high.)

S11 also documents that `elevenlabs agents` holds **two kinds of command** (verbatim table):

| | Workflow commands | API commands |
|---|---|---|
| **What** | `init`, `add`, `status`, `push`, `pull`, `test`, `templates`, `widget embed` | `create`, `get`, `list`, `update`, `delete`, `duplicate`, `run_tests`, and subgroups like `branches`, `tools`, `tests`, `conversations` |
| **Operates on** | Your local project files, syncing them with ElevenLabs | The API directly — one command, one request |
| **Arguments** | Positional, e.g. `agents test <agent_id>` | Flags, e.g. `agents get --agent-id <id>` |
| **Output** | Progress text | The API response (`--format json\|table\|yaml\|csv`) |

Consequences, verbatim: "**Listing** — `agents list` is the API's list of agents in your workspace. For what's configured *locally*, use `agents status`." and "**Deleting** — `agents delete --agent-id <id>` deletes remotely (API command). It does **not** remove the local config file or its `agents.json` entry; delete those yourself."

Useful for a hackathon: `elevenlabs agents create ...` exists as a **direct API command** too (one command, one request), so the CLI can create an agent without a project scaffold.

### 2.5 On-disk project layout (S1, S11 — identical)

```
your_project/
├── agents.json              # Central agent configuration registry
├── tools.json               # Tool definitions registry
├── tests.json               # Test definitions registry
├── agent_configs/           # Agent configuration files
├── tool_configs/            # Tool configuration files
└── test_configs/            # Test configuration files
```

S11's annotation of the same tree is more precise: `agents.json # Agent registry: ids + branch mappings → config paths`.

S11 verbatim on round-tripping: "Manage Conversational AI agents from local configuration files. `elevenlabs agents init` scaffolds a project; agent configs live as JSON on disk and sync to ElevenLabs. **Pulled configs are stored as raw wire JSON and pushed back verbatim, so they round-trip losslessly.**"

That last sentence is load-bearing: the file in `agent_configs/*.json` is *exactly* the REST wire body, so anything learnable from the API reference is directly usable in the CLI config file and vice versa.

### 2.6 `agents.json` registry schema (S13 — CLI source, verbatim struct definitions)

From `cli/elevenlabs/workflow/project.rs`:

```rust
pub const AGENTS_FILE: &str = "agents.json";

/// `agents.json` — the agent registry.
pub struct AgentsConfig {
    pub agents: Vec<AgentDefinition>,
}

/// One entry in `agents.json`.
pub struct AgentDefinition {
    /// Path to the agent's config file, relative to the project root.
    pub config: String,
    pub id: Option<String>,
    pub branch_id: Option<String>,
    pub version_id: Option<String>,
    /// Per-branch configs, keyed by branch name.
    pub branches: Option<BTreeMap<String, BranchDefinition>>,
}

pub struct BranchDefinition {
    /// Path to this branch's config file, relative to the project root.
    pub config: String,
    pub branch_id: String,
    pub version_id: Option<String>,
}

/// `tools.json` — the tool registry.
pub struct ToolsConfig { pub tools: Vec<ToolDefinition> }

/// One entry in `tools.json`.
pub struct ToolDefinition {
    /// `"webhook"` or `"client"`.
    #[serde(rename = "type")]
    pub tool_type: String,
    /// Path to the tool's config file, relative to the project root.
    pub config: String,
    pub id: Option<String>,
}
```

So the JSON shape is:

```json
{
  "agents": [
    {
      "config": "agent_configs/letterlens.json",
      "id": "agent_...",
      "branch_id": "...",
      "version_id": "...",
      "branches": {
        "staging": { "config": "agent_configs/letterlens.staging.json", "branch_id": "..." }
      }
    }
  ]
}
```

```json
{
  "tools": [
    { "type": "webhook", "config": "tool_configs/get_weather.json", "id": "tool_..." }
  ]
}
```

Optional fields are omitted when absent (`skip_serializing_if = "Option::is_none"`). S13 also notes: "Config paths in agents.json / tools.json / tests.json must stay inside the project." Indentation on write is 4 spaces (`PrettyFormatter::with_indent(b"    ")`).

### 2.7 Templates (S1)

Verbatim: "The CLI provides six pre-built templates for common use cases."

* **default** — "Complete configuration with all available fields, sensible defaults, full voice/text support, widget customization, and evaluation criteria."
* **minimal** — "Essential fields only including basic prompt, language, TTS, and conversation settings."
* **voice-only** — "Optimized for voice interactions with disabled text input and advanced voice settings."
* **text-only** — "Text-focused conversations with disabled voice features."
* **customer-service** — "Professional empathetic prompts, low temperature (0.1), 30-minute duration, and evaluation criteria."
* **assistant** — "General-purpose AI assistant with balanced creativity (temperature 0.3) and versatile voice/text support."

```bash
elevenlabs agents add "Agent Name" [options]
```

Options, verbatim: `--template <type>`: "Choose from available templates (default: default)"; `--skip-upload`: "Create locally without uploading to platform".

```bash
elevenlabs agents add "Customer Support Bot" --template customer-service
```

```bash
elevenlabs agents templates list
elevenlabs agents templates show <template>
```

### 2.8 VERBATIM agent config JSON — the `default` template

S1 shows an abridged config. The **complete, authoritative** default template is the CLI's own embedded constant, verbatim from S12 (`cli/elevenlabs/workflow/templates.rs`, `DEFAULT_TEMPLATE_JSON`):

```json
{
  "name": "",
  "conversation_config": {
    "asr": { "quality": "high", "provider": "scribe_realtime", "user_input_audio_format": "pcm_16000", "keywords": [] },
    "turn": { "turn_timeout": 7.0, "silence_end_call_timeout": -1.0, "mode": "turn" },
    "tts": {
      "model_id": "eleven_flash_v2",
      "voice_id": "cjVigY5qzO86Huf0OWal",
      "supported_voices": [],
      "agent_output_audio_format": "pcm_16000",
      "optimize_streaming_latency": 3,
      "stability": 0.5,
      "speed": 1.0,
      "similarity_boost": 0.8,
      "pronunciation_dictionary_locators": []
    },
    "conversation": { "text_only": false, "max_duration_seconds": 600, "client_events": ["audio", "interruption"] },
    "language_presets": {},
    "agent": {
      "first_message": "",
      "language": "en",
      "dynamic_variables": { "dynamic_variable_placeholders": {} },
      "prompt": {
        "prompt": "",
        "llm": "gemini-2.5-flash",
        "temperature": 0.0,
        "max_tokens": -1,
        "tool_ids": [],
        "mcp_server_ids": [],
        "native_mcp_server_ids": [],
        "knowledge_base": [],
        "ignore_default_personality": false,
        "rag": {
          "enabled": false,
          "embedding_model": "e5_mistral_7b_instruct",
          "max_vector_distance": 0.6,
          "max_documents_length": 50000,
          "max_retrieved_rag_chunks_count": 20
        },
        "custom_llm": null
      }
    }
  },
  "platform_settings": {
    "auth": { "enable_auth": false, "allowlist": [], "shareable_token": null },
    "evaluation": { "criteria": [] },
    "widget": {
      "variant": "full",
      "placement": "bottom-right",
      "expandable": "never",
      "avatar": { "type": "orb", "color_1": "#2792dc", "color_2": "#9ce6e6" },
      "feedback_mode": "none",
      "bg_color": "#ffffff",
      "text_color": "#000000",
      "btn_color": "#000000",
      "btn_text_color": "#ffffff",
      "border_color": "#e1e1e1",
      "focus_color": "#000000",
      "shareable_page_show_terms": true,
      "show_avatar_when_collapsed": false,
      "disable_banner": false,
      "mic_muting_enabled": false,
      "transcript_enabled": false,
      "text_input_enabled": true,
      "text_contents": { "main_label": null, "start_call": null, "new_call": null, "end_call": null, "mute_microphone": null, "change_language": null, "collapse": null, "expand": null, "copied": null, "accept_terms": null, "dismiss_terms": null, "listening_status": null, "speaking_status": null, "connecting_status": null, "input_label": null, "input_placeholder": null, "user_ended_conversation": null, "agent_ended_conversation": null, "conversation_id": null, "error_occurred": null, "copy_id": null },
      "language_selector": false,
      "supports_text_only": true,
      "language_presets": {},
      "styles": { "base": null, "base_hover": null, "base_active": null, "base_border": null, "base_subtle": null, "base_primary": null, "base_error": null, "accent": null, "accent_hover": null, "accent_active": null, "accent_border": null, "accent_subtle": null, "accent_primary": null, "overlay_padding": null, "button_radius": null, "input_radius": null, "bubble_radius": null, "sheet_radius": null, "compact_sheet_radius": null, "dropdown_sheet_radius": null },
      "border_radius": null, "btn_radius": null, "action_text": null, "start_call_text": null,
      "end_call_text": null, "expand_text": null, "listening_text": null, "speaking_text": null,
      "shareable_page_text": null, "terms_text": null, "terms_html": null, "terms_key": null,
      "override_link": null, "custom_avatar_path": null
    },
    "data_collection": {},
    "overrides": {
      "conversation_config_override": {
        "tts": { "voice_id": false },
        "conversation": { "text_only": true },
        "agent": { "first_message": false, "language": false, "prompt": { "prompt": false } }
      },
      "custom_llm_extra_body": false,
      "enable_conversation_initiation_client_data_from_webhook": false
    },
    "call_limits": { "agent_concurrency_limit": -1, "daily_limit": 100000, "bursting_enabled": true },
    "privacy": {
      "record_voice": true, "retention_days": -1, "delete_transcript_and_pii": false,
      "delete_audio": false, "apply_to_existing_conversations": false, "zero_retention_mode": false
    },
    "workspace_overrides": {
      "webhooks": { "post_call_webhook_id": null },
      "conversation_initiation_client_data_webhook": null
    },
    "safety": { "is_blocked_ivc": false, "is_blocked_non_ivc": false, "ignore_safety_evaluation": false },
    "testing": { "attached_tests": [] },
    "ban": null
  },
  "tags": []
}
```

`default_template()` then sets `name` and `conversation_config.agent.prompt.prompt` to `"You are {name}, a helpful AI assistant."` (S12).

**Mapping to the dimensions asked for:**

| Asked-for field | Exact path | Confirmed by |
|---|---|---|
| name | `name` (top level) | S1, S3, S12 |
| system prompt | `conversation_config.agent.prompt.prompt` | S1, S3, S12 |
| LLM | `conversation_config.agent.prompt.llm` | S1, S3, S12 |
| first message | `conversation_config.agent.first_message` | S3, S12 |
| language | `conversation_config.agent.language` | S1, S3, S12 |
| voice | `conversation_config.tts.voice_id` | S1, S3, S12 |
| TTS model | `conversation_config.tts.model_id` | S1, S3, S12 |
| ASR | `conversation_config.asr.{quality,provider,user_input_audio_format,keywords}` | S1, S3, S12 |
| turn detection | `conversation_config.turn.{turn_timeout,silence_end_call_timeout,mode,...}` | S3, S12 |
| tools | `conversation_config.agent.prompt.tool_ids` (array of IDs) | S3, S8, S9, S12 |

### 2.9 VERBATIM — the `minimal` template (S12)

```json
{
  "name": "<name>",
  "conversation_config": {
    "agent": {
      "prompt": {
        "prompt": "You are <name>, a helpful AI assistant.",
        "llm": "gemini-2.5-flash",
        "temperature": 0.0
      },
      "language": "en"
    },
    "conversation": {
      "text_only": false
    },
    "tts": {
      "model_id": "eleven_flash_v2",
      "voice_id": "cjVigY5qzO86Huf0OWal"
    }
  },
  "platform_settings": {},
  "tags": []
}
```

This is the smallest config the CLI itself ships — a good starting point for LetterLens.

Derived templates (S12, verbatim mutations of `default`):

* `voice-only`: `conversation_config.conversation.text_only = false`, `platform_settings.widget.supports_text_only = false`, `platform_settings.widget.text_input_enabled = false`
* `text-only`: `conversation_config.conversation.text_only = true`, `platform_settings.widget.supports_text_only = true`
* `customer-service`: `prompt.temperature = 0.1`, `conversation.max_duration_seconds = 1800`, `platform_settings.call_limits.daily_limit = 10000`, populated `platform_settings.evaluation.criteria`, `tags = ["customer-service"]`
* `assistant`: `prompt.temperature = 0.3`, `prompt.max_tokens = 1000`, `tags = ["assistant", "general-purpose"]`

### 2.10 Abridged config example as shown on the docs page (S1, verbatim)

```json
{
  "name": "Agent Name",
  "conversation_config": {
    "agent": {
      "language": "en",
      "prompt": {
        "prompt": "You are a helpful AI assistant.",
        "llm": "gemini-2.5-flash",
        "temperature": 0.0
      }
    },
    "tts": {
      "model_id": "eleven_turbo_v2",
      "voice_id": "cjVigY5qzO86Huf0OWal",
      "agent_output_audio_format": "pcm_16000"
    },
    "asr": {
      "provider": "scribe_realtime",
      "quality": "high",
      "user_input_audio_format": "pcm_16000"
    },
    "conversation": {
      "text_only": false,
      "max_duration_seconds": 600,
      "client_events": ["audio", "interruption"]
    }
  },
  "platform_settings": {
    "widget": {
      "variant": "full",
      "placement": "bottom-right"
    }
  },
  "tags": []
}
```

### 2.11 Turn-detection field reference (S3, verbatim `TurnConfig`)

* `turn_timeout` (double, optional, default: 7) — "Maximum wait time for the user's reply before re-engaging the user"
* `initial_wait_time` (double, optional, nullable) — "How long the agent will wait for the user to start the conversation if the first message is empty. If not set, uses the regular turn_timeout."
* `silence_end_call_timeout` (double, optional, default: -1) — "Maximum wait time since the user last spoke before terminating the call"
* `turn_eagerness` (enum, optional, default: `normal`) — "Controls how eager the agent is to respond. Low = less eager (waits longer), Standard = default eagerness, High = more eager (responds sooner)". Allowed values: `patient`, `normal`, `eager`
* `spelling_patience` (enum, optional, default: `auto`) — "Controls if the agent should be more patient when user is spelling numbers and named entities. Auto = model based, Off = never wait extra"

The shipped template also writes `"mode": "turn"` inside `turn` (S12). `mode` is not in the `TurnConfig` field list I captured from S3 — treat `mode` as **medium** confidence and copy it verbatim from the template rather than inventing other values.

### 2.12 ASR field reference (S3, verbatim `ASRConversationalConfig`)

* `quality` (enum, default `high`) — allowed values: `high`
* `provider` (enum, default `scribe_realtime`) — allowed values: `elevenlabs`, `scribe_realtime`
* `user_input_audio_format` (enum, default `pcm_16000`) — allowed: `pcm_8000`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `pcm_48000`, `ulaw_8000`
* `keywords` (list of string) — "Keywords to boost prediction probability for"

`keywords` is worth using in LetterLens for domain terms the ASR will otherwise mangle.

### 2.13 TTS field reference (S3, verbatim `TTSConversationalConfig-Input`)

* `model_id` (enum, default `eleven_flash_v2`) — allowed: `eleven_turbo_v2`, `eleven_turbo_v2_5`, `eleven_flash_v2`, `eleven_flash_v2_5`, `eleven_multilingual_v2`, `eleven_v3_conversational`, `eleven_v4`, `eleven_v4_turbo`
* `voice_id` (string, default `cjVigY5qzO86Huf0OWal`)
* `agent_output_audio_format` (enum, default `pcm_16000`) — same PCM/ulaw list as ASR
* `stability` (default 0.5), `speed` (default 1), `similarity_boost` (default 0.8)
* `expressive_mode` (boolean, default true) — "When enabled, applies expressive audio tags prompt. Automatically disabled for non-v3 models."
* `suggested_audio_tags` — "Suggested audio tags to boost expressive speech (for eleven_v3 and eleven_v3_conversational models). The agent can still use other tags not listed here."
* `text_normalisation_type` (enum, default `system_prompt`) — allowed: `system_prompt`, `elevenlabs`
* `optimize_streaming_latency` — **deprecated**, verbatim: "Deprecated: this field is a no-op and is ignored." (the CLI default template still writes `3` — harmless, but do not rely on it)

### 2.14 Conversation-config field reference (S3, verbatim `ConversationConfig-Input`)

* `text_only` (boolean, default false) — "If enabled audio will not be processed and only text will be used, use to avoid audio pricing."
* `max_duration_seconds` (integer, default 600) — "The maximum duration of a conversation in seconds"
* `client_events` (list of enum) — "The events that will be sent to the client". Allowed values, verbatim and complete:

```
conversation_initiation_metadata, asr_initiation_metadata, ping, audio, interruption,
user_transcript, tentative_user_transcript, agent_response, agent_response_correction,
client_tool_call, mcp_tool_call, mcp_connection_status, agent_tool_request,
agent_tool_response, agent_tool_response_full_payload, agent_response_metadata, vad_score,
agent_chat_response_part, client_error, guardrail_triggered, dtmf_request,
agent_response_complete, context_usage, internal_turn_probability,
internal_tentative_agent_response
```

* `file_input` (FileInputConfig) — "Configuration for file input (image/PDF uploads) during conversations." **Directly relevant to LetterLens** — this is how a letter image/PDF reaches the agent mid-conversation. I did not fetch the `FileInputConfig` sub-schema; treat its internals as unconfirmed.
* `monitoring_enabled` (boolean, default false) — "Enable real-time monitoring of conversations via WebSocket"; `monitoring_events` takes the same enum as `client_events`
* `dtmf_input_settings`, `background_sound`, `source_attribution` (boolean, default false) — "When enabled and knowledge base content is present, the LLM is instructed to report which sources it used."

### 2.15 CI/CD (S1, verbatim)

```yml
# In your GitHub Actions workflow
- name: Deploy ElevenAgents agents
  run: |
    npm install -g @elevenlabs/cli
    export ELEVENLABS_API_KEY=${{ secrets.ELEVENLABS_API_KEY }}
    elevenlabs agents push --dry-run  # Preview changes
    elevenlabs agents push            # Deploy
    elevenlabs agents status          # Verify deployment
```

### 2.16 Widget embed (S1, verbatim)

```bash
elevenlabs agents widget embed <agent_id>
```

outputs

```html
<elevenlabs-convai agent-id="agent_id_here"></elevenlabs-convai>
<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async></script>
```

---

## 3. Attaching a CUSTOM LLM in the agent config JSON

### 3.1 The two fields (S3 + S12 — high confidence)

Two things must be set together:

1. `conversation_config.agent.prompt.llm` = **`"custom-llm"`** — this exact string is in the `llm` enum's allowed values (S3).
2. `conversation_config.agent.prompt.custom_llm` = an object.

S3 verbatim on the field:

> * `custom_llm` (CustomLLM, optional, nullable) — Definition for a custom LLM if LLM field is set to 'CUSTOM_LLM'

The default CLI template writes `"custom_llm": null` (S12), confirming the path `conversation_config.agent.prompt.custom_llm`.

### 3.2 `CustomLLM` type — verbatim field list (S3)

```
### CustomLLM

- `url` (string, required) — The URL of the Chat Completions compatible endpoint
- `model_id` (string, optional, nullable) — The model ID to be used if URL serves multiple models
- `api_key` (CustomLlmApiKey, optional, nullable) — The API key for authentication. Either a workspace secret reference {'secret_id': '...'} or an environment variable reference {'env_var_label': '...'}.
- `auth_connection` (CustomLlmAuthConnection, optional, nullable) — Optional workspace auth connection for authentication. Only auth connections that produce an Authorization Bearer token are supported; Basic auth, mTLS, custom header, and URL secret auth connections are not supported.
- `request_headers` (map from string to CustomLlmRequestHeaders, optional) — Headers that should be included in the request
- `api_version` (string, optional, nullable) — The API version to use for the request
- `api_type` (enum, optional, default: chat_completions) — The API type to use (chat_completions, responses or websocket)
  - Allowed values: `chat_completions`, `responses`, `websocket`
```

**Critical gotcha:** `api_key` is **NOT a raw string**. Verbatim: "Either a workspace secret reference `{'secret_id': '...'}` or an environment variable reference `{'env_var_label': '...'}`." You must create a workspace secret first and reference it by id.

### 3.3 Resulting JSON (composed from the verbatim field list above)

```json
{
  "conversation_config": {
    "agent": {
      "prompt": {
        "prompt": "You are the LetterLens assistant.",
        "llm": "custom-llm",
        "temperature": null,
        "custom_llm": {
          "url": "https://letterlens.example.com/v1",
          "model_id": "letterlens-router",
          "api_key": { "secret_id": "<workspace secret id>" },
          "api_type": "chat_completions",
          "request_headers": {}
        }
      }
    }
  }
}
```

Two notes from S3 worth copying into code:

* `temperature` (double, optional, nullable, default: 0) — verbatim: "Set to null to omit the parameter from the LLM request entirely (useful for custom LLMs that reject the temperature field)." **Set `temperature: null` for a custom LLM unless you know it accepts the field.**
* `url` is "The URL of the Chat Completions compatible endpoint" — i.e. the base that ElevenLabs appends the path to, per S6 which says the server endpoint is `/v1/chat/completions`.

Confidence: **high** on `llm: "custom-llm"`, the `custom_llm` path, and every field name/enum above (all from the API reference type listing). **Medium** on whether `url` should include the `/v1` suffix or the full `/v1/chat/completions` path — the docs say "The URL of the Chat Completions compatible endpoint" (S3) and separately that the server must implement `/v1/chat/completions` (S6), but no page I fetched shows a verbatim `url` value. Test both.

### 3.4 Custom LLM server contract (S6, verbatim)

> "To bring a custom LLM server, set up a compatible server endpoint using OpenAI's style. You can implement either the Chat Completions API (`/v1/chat/completions`) or the Responses API (`/v1/responses`).
>
> Both endpoints must return responses in SSE (Server-Sent Events) format with `Content-Type: text/event-stream`."

> "The Chat Completions API uses the `/v1/chat/completions` endpoint. Each chunk must be formatted as `data: {json}\n\n` and the stream must end with `data: [DONE]\n\n`."

Dashboard route (S6, verbatim): "In your Agent settings in the ElevenLabs dashboard, select \"Custom LLM\" from the \"LLM\" dropdown menu on the right." … "Enter the server URL and the Model ID of your custom LLM server." … "Click the dropdown under \"API key\" and select \"Create new secret\". Name the key `OPENAI_API_KEY` and add the key to the \"value\" field and click \"Add secret\"." … "Click the \"x\" button to close the LLM modal and click \"Publish\" to save your changes."

Reasoning on custom endpoints (S6, verbatim): "Stream reasoning in the `reasoning` or `reasoning_content` field of each response delta." For Responses API: "Return a `reasoning` output item with the summary text in its `summary` field." And: "With reasoning effort configured and Reasoning summary enabled, ElevenLabs sets `reasoning.summary` to `auto` in the request." For Gemini-compatible endpoints: "ElevenLabs requests thoughts with `google.thinking_config.include_thoughts` and reads content marked with `extra_content.google.thought`."

S6 also documents built-in **system tools integration** for custom LLM servers (sections: End call, Language detection, Agent transfer, Transfer to human, Skip turn, Voicemail detection) and **Custom LLM Parameters** via extra body — gated server-side by `platform_settings.overrides.custom_llm_extra_body` (which the shipped template sets to `false`, S12).

> **Not confirmed:** S6 does *not* show a JSON agent-config snippet for custom LLM at all — it is a dashboard walkthrough plus server code. The JSON field names in §3.2/§3.3 come from the Create-agent API reference (S3), which is the authoritative schema for the same wire body the CLI writes (S11: configs "round-trip losslessly").

---

## 4. REST API: `POST /v1/convai/agents/create`

### 4.1 Endpoint and servers (S3, verbatim)

```
# Create agent

POST https://api.elevenlabs.io/v1/convai/agents/create
Content-Type: application/json

Create an agent from a config object
```

Servers (verbatim):

* `https://api.elevenlabs.io` (Production, default)
* `https://api.us.elevenlabs.io` (Production US)
* `https://api.eu.residency.elevenlabs.io` (Production EU)
* `https://api.in.residency.elevenlabs.io` (Production India)
* `https://api.sg.residency.elevenlabs.io` (Production Singapore)

### 4.2 Auth header (S10 + S14)

S10 verbatim: "All API requests should include your API key in an `xi-api-key` HTTP header as follows:"

```bash
xi-api-key: ELEVENLABS_API_KEY
```

S10 verbatim example:

```bash
curl 'https://api.elevenlabs.io/v1/models' \
  -H 'Content-Type: application/json' \
  -H 'xi-api-key: $ELEVENLABS_API_KEY'
```

S14 (live OpenAPI spec) confirms the parameter on this exact operation:

```json
{"name": "xi-api-key", "in": "header", "required": false,
 "schema": {"anyOf": [{"type": "string"}, {"type": "null"}],
 "description": "Your API key. This is required by most endpoints to access our API programmatically. You can view your xi-api-key using the 'Profile' tab on the website."}}
```

Note it is marked `required: false` in the spec and the spec has **no `securitySchemes`** — that is a spec artefact, not permission to omit it. S10 says every request must include it.

S10 verbatim on key restrictions: "**Scope restriction:** Set access restrictions by limiting which API endpoints the key can access."; "**Credit quota:** Define custom credit limits to control usage."; "**IP allowlisting:** Restrict the key to specific IP addresses or CIDR ranges. Requests from non-allowlisted IPs are rejected with a `403` error."

S10 verbatim on client-side use: "**Remember that your API key is a secret.** Do not share it with others or expose it in any client-side code (browsers, apps)." and "For certain endpoints, you can use single use tokens to authenticate your requests. These tokens are valid for a limited time and can be used to connect to the API without exposing your API key, for example from the client side." (`/docs/api-reference/tokens/create`)

### 4.3 Request body (S3, verbatim)

```
### Body (application/json)

This endpoint expects a Body_Create_Agent_v1_convai_agents_create_post.

- `conversation_config` (ConversationalConfigAPIModel-Input, required) — Conversation configuration for an agent
- `platform_settings` (AgentPlatformSettingsRequestModel, optional, nullable) — Platform settings for the agent are all settings that aren't related to the conversation orchestration and content.
- `workflow` (AgentWorkflowRequestModel, optional) — Workflow for the agent. This is used to define the flow of the conversation and how the agent interacts with tools.
- `name` (string, optional, nullable) — A name to make the agent easier to find
- `tags` (list of string, optional, nullable) — Tags to help classify and filter the agent
```

`conversation_config` is the **only required** top-level field. Its sub-objects (S3, verbatim):

```
### ConversationalConfigAPIModel-Input

- `asr` (ASRConversationalConfig, optional) — Configuration for conversational transcription
- `turn` (TurnConfig, optional) — Configuration for turn detection
- `tts` (TTSConversationalConfig-Input, optional) — Configuration for conversational text to speech
- `conversation` (ConversationConfig-Input, optional) — Configuration for conversational events
- `language_presets` (map from string to LanguagePreset-Input, optional) — Language presets for conversations
- `vad` (VADConfig, optional) — Configuration for voice activity detection
- `agent` (AgentConfigAPIModel-Input, optional) — Agent specific configuration
```

Query param (S3, verbatim): `enable_versioning` (boolean, optional, default: true, **deprecated**) — "Deprecated: all agents are versioned. This parameter is ignored."

### 4.4 Response (S3, verbatim)

```
### 200
Successful Response
- `agent_id` (string, required) — ID of the created agent
```

Errors: `422 Unprocessable Entity Error` — Validation Error, `detail` (list of ValidationError, each with `loc`, `msg`, `type`).

### 4.5 Verbatim curl example from the docs

The docs page's generated sample is minimal (extracted from the HTML of S3, verbatim):

```bash
curl -X POST https://api.elevenlabs.io/v1/convai/agents/create \
     -H "Content-Type: application/json" \
     -d '{
  "conversation_config": {}
}'
```

Note the generated sample **omits** `xi-api-key` (because the spec declares no security scheme). The usable form for LetterLens — **field names and enum values all verbatim from S3/S12, composition mine**:

```bash
curl -X POST https://api.elevenlabs.io/v1/convai/agents/create \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LetterLens",
    "tags": ["letterlens", "hackathon"],
    "conversation_config": {
      "agent": {
        "first_message": "Hi, I am LetterLens. Hold a letter up and tell me what you need.",
        "language": "en",
        "timezone": "Europe/London",
        "prompt": {
          "prompt": "You are LetterLens, a calm assistant that explains official letters in plain language.",
          "llm": "gemini-2.5-flash",
          "temperature": 0.0,
          "tool_ids": []
        }
      },
      "tts": { "model_id": "eleven_flash_v2", "voice_id": "cjVigY5qzO86Huf0OWal" },
      "asr": { "provider": "scribe_realtime", "quality": "high", "user_input_audio_format": "pcm_16000" },
      "turn": { "turn_timeout": 7.0 },
      "conversation": { "text_only": false, "max_duration_seconds": 600, "client_events": ["audio", "interruption"] }
    }
  }'
```

### 4.6 SDK equivalents (S2, verbatim)

Python:

```python
response = elevenlabs.conversational_ai.agents.create(
    name="My voice agent",
    tags=["test"], # List of tags to help classify and filter the agent
    conversation_config={
        "tts": {
            "voice_id": "aMSt68OGf4xUZAnLpTU8",
            "model_id": "eleven_flash_v2"
        },
        "agent": {
            "first_message": "Hi, this is Rachel from [Your Company Name] support. How can I help you today?",
            "prompt": {
                "prompt": prompt,
            }
        }
    }
)

print("Agent created with ID:", response.agent_id)
```

TypeScript:

```typescript
const agent = await elevenlabs.conversationalAi.agents.create({
    name: "My voice agent",
    tags: ["test"], // List of tags to help classify and filter the agent
    conversationConfig: {
        tts: {
            voiceId: "aMSt68OGf4xUZAnLpTU8",
            modelId: "eleven_flash_v2",
        },
        agent: {
            firstMessage: "Hi, this is Rachel from [Your Company Name] support. How can I help you today?",
            prompt: {
                prompt,
            }
        },
    },
});

console.log(`Agent created with ID: ${agent.agentId}`);
```

The SDKs are camelCase in TS, snake_case in Python; the **wire/CLI JSON is snake_case**.

Clients (S10, verbatim): Python `from elevenlabs.client import ElevenLabs` / `ElevenLabs(api_key='YOUR_API_KEY')`; Node `import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";` / `new ElevenLabsClient({ apiKey: "YOUR_API_KEY" })`.

S2 verbatim note: "The agent created above will have a `\"test\"` tag, this is useful to help classify and filter the agent. For example distinguishing between test agents and production agents."

Run commands (S2, verbatim): `python create_agent.py` / `npx tsx createAgent.mts`.

---

## 5. How tools are attached in 2026 — **reusable tools + `tool_ids`**, NOT inline

### 5.1 The deprecation, verbatim (S3)

From `PromptAgentAPIModel-Input`:

```
- `tool_ids` (list of string, optional) — A list of IDs of tools used by the agent
...
- `tools` (list of PromptAgentApiModelInputToolsItems, optional, deprecated) — A list of tools that the agent can use over the course of the conversation, use tool_ids instead
```

**That is the answer: `prompt.tools` is deprecated; use `prompt.tool_ids`.** Tools are created separately as workspace-level reusable resources via `POST /v1/convai/tools`, then referenced by ID.

The CLI's own default template agrees — it emits `"tool_ids": []` and no `tools` key at all (S12).

S4 verbatim on what a tool is: `POST /v1/convai/tools` — "Add a new tool to the available tools in the workspace." Workspace-scoped, i.e. reusable across agents. The spec also exposes `/v1/convai/tools/{tool_id}/dependent-agents` (S14), which only makes sense for shared-by-reference tools.

### 5.2 Current correct flow, verbatim from the docs (S8 webhook, S9 client)

Both pages use the identical three-step shape: **create the tool → take its `id` → put the id in `prompt.tool_ids`**.

**CLI route — webhook tool (S8, verbatim).** Save as `tool_configs/get_weather.json`:

```json
{
  "type": "webhook",
  "name": "get_weather",
  "description": "Gets the current weather forecast for a location",
  "api_schema": {
    "url": "https://api.open-meteo.com/v1/forecast?current=temperature_2m,wind_speed_10m",
    "method": "GET",
    "path_params_schema": {
      "latitude": {
        "type": "string",
        "description": "The latitude coordinate for the requested location"
      },
      "longitude": {
        "type": "string",
        "description": "The longitude coordinate for the requested location"
      }
    }
  }
}
```

```bash
elevenlabs tools add "get_weather" --type "webhook" --config-path ./tool_configs/get_weather.json
```

Verbatim: "Edit `agent_configs/<agent-name>.json` and add the tool's ID to `conversation_config.agent.prompt.tool_ids`, then push:"

```bash
elevenlabs agents push --agent "<agent-name>"
```

**CLI route — client tool (S9, verbatim).** Save as `tool_configs/log_message.json`:

```json
{
  "type": "client",
  "name": "logMessage",
  "description": "Use this client-side tool to log a message to the user's client.",
  "expects_response": false,
  "parameters": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "The message to log in the console."
      }
    },
    "required": ["message"]
  }
}
```

```bash
elevenlabs tools add "logMessage" --type "client" --config-path ./tool_configs/log_message.json
```

Verbatim: "Edit `agent_configs/<agent-name>.json` to add the tool's ID to `conversation_config.agent.prompt.tool_ids`, then push".

> Note the **CLI tool config file is unwrapped** — `type`/`name`/`description`/`api_schema` at the top level. The REST body wraps the same object in `tool_config` (see §5.3). This asymmetry is real and easy to get wrong.

**API route (S8/S9, verbatim Python):**

```python
from elevenlabs import ElevenLabs, ToolRequestModel

elevenlabs = ElevenLabs()

tool = elevenlabs.conversational_ai.tools.create(
    request=ToolRequestModel(
        tool_config={
            "type": "webhook",
            "name": "get_weather",
            "description": "Gets the current weather forecast for a location",
            "api_schema": {
                "url": "https://api.open-meteo.com/v1/forecast?current=temperature_2m,wind_speed_10m",
                "method": "GET",
                "path_params_schema": {
                    "latitude": {
                        "type": "string",
                        "description": "The latitude coordinate for the requested location",
                    },
                    "longitude": {
                        "type": "string",
                        "description": "The longitude coordinate for the requested location",
                    },
                },
            },
        }
    )
)

elevenlabs.conversational_ai.agents.update(
    agent_id="agent_7101k5zvyjhmfg983brhmhkd98n6",
    conversation_config={
        "agent": {"prompt": {"tool_ids": [tool.id]}},
    },
)
```

Client-tool variant of the same call (S9, verbatim):

```python
tool = elevenlabs.conversational_ai.tools.create(
    request=ToolRequestModel(
        tool_config={
            "type": "client",
            "name": "logMessage",
            "description": "Use this client-side tool to log a message to the user's client.",
            "expects_response": False,
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to log in the console.",
                    }
                },
                "required": ["message"],
            },
        }
    )
)
```

TypeScript equivalent (S8, verbatim shape): `elevenlabs.conversationalAi.tools.create({ toolConfig: { type: "webhook", name: "get_weather", description: "...", apiSchema: { url, method: "GET", pathParamsSchema: {...} } } })`.

### 5.3 `POST /v1/convai/tools` — endpoint and body (S4, verbatim)

```
# Create tool

POST https://api.elevenlabs.io/v1/convai/tools
Content-Type: application/json

Add a new tool to the available tools in the workspace.
```

```
### Body (application/json)

This endpoint expects a ToolRequestModel.

- `tool_config` (ToolRequestModelToolConfig, required) — Configuration for the tool
- `response_mocks` (list of ToolResponseMockConfig-Input, optional, nullable) — Mock responses with optional parameter conditions. Evaluated top-to-bottom; first match wins.
```

```
### 200
Successful Response
- `id` (string, required)
- `tool_config` (ToolResponseModelToolConfig, required) — The type of tool
- `access_info` (ResourceAccessInfo, required)
- `usage_stats` (ToolUsageStatsResponseModel, required)
- `response_mocks` (list of ToolResponseMockConfig-Output, optional, nullable) — Mock responses with optional parameter conditions. Evaluated top-to-bottom; first match wins.
```

The response's `id` is what goes into `prompt.tool_ids`.

`tool_config` is a discriminated union on `type`. Verbatim for `type: "client"` (S4):

* `description` (string, required) — "Description of when the tool should be used and what it does."
* `name` (string, required)
* `assignments` (list of DynamicVariableAssignment, optional) — "Configuration for extracting values from tool responses and assigning them to dynamic variables"
* `dynamic_variables` (DynamicVariablesConfig, optional) — "Configuration for dynamic variables"
* `execution_mode` (enum, default `immediate`) — "Determines when and how the tool executes: 'immediate' executes the tool right away when requested by the LLM, 'post_tool_speech' waits for the agent to finish speaking before executing, 'async' runs the tool in the background without blocking - best for long-running operations." Allowed: `immediate`, `post_tool_speech`, `async`
* `expects_response` (boolean, default false) — "If true, calling this tool should block the conversation until the client responds with some response which is passed to the llm. If false then we will continue the conversation without waiting for the client to respond, this is useful to show content to a user but not block the conversation"
* `interruption_mode` (enum, default `allow`) — "Controls whether the user can interrupt the agent around this tool call. 'allow' (default) lets the user interrupt at any time, 'disable_during_tool' suppresses interruptions only while the tool is running, 'disable_during_tool_and_turn' suppresses interruptions while the tool runs and for the agent response that follows it." Allowed: `allow`, `disable_during_tool`, `disable_during_tool_and_turn`
* `parameters` (ObjectJsonSchemaProperty-Input, optional, nullable) — "Schema for any parameters to pass to the client"
* `pre_tool_speech` (enum, default `auto`) — "Controls whether the agent speaks before this tool is called. 'auto' (default) decides based on recent tool latency, 'force' always asks the agent to speak, 'off' fully opts out regardless of latency." Allowed: `auto`, `force`, `off`
* `response_timeout_secs` (integer, default 20) — "Must be between 1 and 120 seconds (inclusive)."
* `tool_call_sound` (enum, nullable) — "Predefined tool call sound type to play during tool execution. If not specified, no tool call sound will be played." Allowed: `typing`, `elevator1`, `elevator2`, `elevator3`, `elevator4`

Verbatim for `type: "webhook"` (S4) — same core fields plus:

* `api_schema` (WebhookToolApiSchemaConfig-Input, **required**) — "The schema for the outgoing webhoook, including parameters and URL specification" [typo is in the docs]
* `api_schema.url` (string, required) — "The URL that the webhook will be sent to. May include path parameters, e.g. `https://example.com/agents/{agent_id}`"
* `follow_redirects` (boolean, default false) — "Whether to resolve a redirect from the endpoint and return the final response. One redirect is followed, as a GET without the request body; nothing configured on this tool (headers, authentication, client certificate) is sent to the redirect target. Both the endpoint and the redirect target must use HTTPS. Not supported for API integration tools."
* `follow_redirects_allowed_domains` (list of string) — "Domains a redirect may point at, e.g. 'test.example.com'. Required when following redirects, and a target outside the list is refused."
* `response_timeout_secs` (integer, default 20) — for webhook tools "Must be between **5 and 300** seconds (inclusive)." (different range from client tools)
* `tool_call_sound_behavior` (enum, default `auto`) — "Determines when the tool call sound should play. 'auto' only plays when there's pre-tool speech, 'always' plays for every tool call." Allowed: `auto`, `always`
* `tool_error_handling_mode` (enum, default `auto`) — "Controls how tool errors are processed before being shared with the agent. 'auto' determines handling based on tool type (summarized for native integrations, hide for others), 'summarized' sends an LLM-generated summary, 'passthrough' sends the raw error, 'hide' does not share the error with the agent." Allowed: `auto`, `summarized`, `passthrough`, `hide`
* **deprecated:** `disable_interruptions` ("DEPRECATED: use `interruption_mode` instead. If true, the user will not be able to interrupt the agent while this tool is running."), `force_pre_tool_speech` ("DEPRECATED: use `pre_tool_speech` instead. If true, the agent will speak before the tool call.")

Other tool endpoints in the live spec (S14): `/v1/convai/tools`, `/v1/convai/tools/{tool_id}`, `/v1/convai/tools/{tool_id}/dependent-agents`, `/v1/convai/tools/{tool_id}/executions`.

### 5.4 Tool kinds available (S7, verbatim)

* **Client Tools** — "Tools executed directly on the client-side application (e.g., web browser, mobile app)."
* **Webhook tools** — "Custom tools that call external APIs through webhooks."
* **Code Tools** — "Custom JavaScript executed in a sandboxed environment on ElevenLabs' infrastructure."
* **MCP Tools** — "Model Context Protocol servers that provide tools and resources to agents."
* **System Tools** — "Built-in tools provided by the platform for common actions."

Tool features (S7, verbatim): "**Tool Call Sounds** — Add ambient audio during tool execution to enhance user experience."; "**Tool Interruptions** — Control whether users can interrupt the agent while a tool runs."

MCP servers attach via separate arrays, not `tool_ids` (S3): `mcp_server_ids` ("A list of MCP server ids to be used by the agent") and `native_mcp_server_ids` ("A list of Native MCP server ids to be used by the agent"). System tools attach via `built_in_tools` (S3: "`built_in_tools` (BuiltInTools-Input, optional) — Built-in system tools to be used by the agent"). The CLI only manages `webhook` and `client` tool types (S11: "Manage the webhook and client tools your agents reference").

Also relevant (S3): `enable_parallel_tool_calls` (boolean, default true) — "Enable parallel tool calling. When enabled, the agent can execute multiple tools in parallel within a single turn. Not supported by all models."

---

## 6. Native LLM options — verbatim model identifiers

### 6.1 Wire identifiers (S3 — the `prompt.llm` enum, verbatim and complete)

These are the strings you put in `conversation_config.agent.prompt.llm`:

```
gpt-4o-mini, gpt-4o, gpt-4, gpt-4-turbo, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano,
gpt-5, gpt-5.1, gpt-5.2, gpt-5.2-chat-latest, gpt-5.4, gpt-5.4-mini, gpt-5.4-nano,
gpt-5.5, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, gpt-6-astra, gpt-6-sol, gpt-6-luna,
gpt-5-mini, gpt-5-nano, gpt-3.5-turbo,
gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash, gemini-2.0-flash-lite,
gemini-2.5-flash-lite, gemini-2.5-flash, gemini-3-pro-preview, gemini-3-flash-preview,
gemini-3.1-pro-preview, gemini-3.1-flash-lite-preview, gemini-3.1-flash-lite,
gemini-3.5-flash, gemini-3.5-flash-lite, gemini-3.6-flash, gemini-3.7-flash, gemini-3.8-flash,
claude-sonnet-4-5, claude-opus-4-7, claude-opus-4-8, claude-opus-5, claude-opus-5-5,
claude-sonnet-4-6, claude-sonnet-5, claude-sonnet-5-5, claude-sonnet-4, claude-haiku-4-5,
claude-3-7-sonnet, claude-3-5-sonnet, claude-3-5-sonnet-v1, claude-3-haiku,
grok-beta, custom-llm,
qwen3-4b, qwen3-30b-a3b, qwen36-35b-a3b, qwen35-397b-a17b,
gpt-oss-20b, gpt-oss-120b, glm-45-air-fp8, glm-52, deepseek-v41-flash,
gemini-2.5-flash-preview-09-2025, gemini-2.5-flash-lite-preview-09-2025,
gemini-2.5-flash-preview-05-20, gemini-2.5-flash-preview-04-17,
gemini-2.5-flash-lite-preview-06-17, gemini-2.0-flash-lite-001, gemini-2.0-flash-001,
gemini-1.5-flash-002, gemini-1.5-flash-001, gemini-1.5-pro-002, gemini-1.5-pro-001,
claude-sonnet-4@20250514, claude-sonnet-4-5@20250929, claude-haiku-4-5@20251001,
claude-3-7-sonnet@20250219, claude-3-5-sonnet@20240620, claude-3-5-sonnet-v2@20241022,
claude-3-haiku@20240307,
gpt-5-2025-08-07, gpt-5.1-2025-11-13, gpt-5.2-2025-12-11, gpt-5.4-2026-03-05,
gpt-5.4-mini-2026-03-17, gpt-5.4-nano-2026-03-17, gpt-5.5-2026-04-23,
gpt-5-mini-2025-08-07, gpt-5-nano-2025-08-07,
gpt-4.1-2025-04-14, gpt-4.1-mini-2025-04-14, gpt-4.1-nano-2025-04-14,
gpt-4o-mini-2024-07-18, gpt-4o-2024-11-20, gpt-4o-2024-08-06, gpt-4o-2024-05-13,
gpt-4-0613, gpt-4-0314, gpt-4-turbo-2024-04-09, gpt-3.5-turbo-0125, gpt-3.5-turbo-1106,
watt-tool-8b, watt-tool-70b
```

The same enum is reused for `platform_settings.analysis_llm`, per-criterion `llm`, and `backup_llm_config.override.order` (S3).

### 6.2 Human-readable table (S5, verbatim)

S5: "Currently, the following models are natively supported and can be configured via the agent settings:"

| Provider | Model |
|---|---|
| **ElevenLabs** | DeepSeek Flash 4.1 |
| | GLM 5.2 |
| | Qwen3.6-35B-A3B |
| | Qwen3.5-397B-A17B |
| **Google** | Gemini 3.8 Flash, Gemini 3.7 Flash, Gemini 3.6 Flash, Gemini 3.5 Flash, Gemini 3.5 Flash-Lite, Gemini 3.1 Pro Preview, Gemini 3.1 Flash Lite, Gemini 3 Flash Preview, Gemini 2.5 Flash, Gemini 2.5 Flash Lite |
| **OpenAI** | GPT-6.1 Sol, GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, GPT-5.6 Sol, GPT-5.6 Terra, GPT-5.6 Luna, GPT-5.5, GPT-5.4, GPT-5.4 Mini, GPT-5.4 Nano, GPT-5.2, GPT-5.1, GPT-5, GPT-5 Mini, GPT-5 Nano, GPT-4.1, GPT-4.1 Mini, GPT-4.1 Nano, GPT-4o, GPT-4o Mini |
| **Anthropic** | Claude Opus 5.5, Claude Opus 5, Claude Opus 4.8, Claude Opus 4.7, Claude Sonnet 5.5, Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, Claude Haiku 4.5 |

S5 verbatim on the custom option: "Using your own custom LLM is supported by specifying the endpoint we should make requests to and providing credentials through our secure secret storage."

S5 verbatim caveat: "Some models are unavailable when EU data residency is enabled."

> **Mismatch worth knowing:** S5's table lists "GPT-6.1 Sol" but there is **no `gpt-6.1-sol` identifier** in the S3 `llm` enum (only `gpt-6-sol`, `gpt-6-astra`, `gpt-6-luna`). Trust the enum (S3), not the prose table, when writing config. Confidence on the enum: **high**. On "GPT-6.1 Sol" being settable: **low**.

### 6.3 Plan B fallback recommendation

The CLI's own default is **`gemini-2.5-flash`** (S12, both `default` and `minimal` templates) — the safest Plan B value: it is in the enum, it is what ElevenLabs ships as the default, and it is low-latency. `gemini-3.5-flash` / `gemini-3.8-flash` are the newer flash tiers if you want current-gen.

S5 verbatim guidance: "**Latency requirements**: For live voice conversations, choose a low-latency model and measure response time with your prompts and tools".

### 6.4 Backup LLM cascading (S3 + S5) — the real Plan B mechanism

`prompt.backup_llm_config` (S3) — "Configuration for backup LLM cascading. Can be disabled, use system defaults, or specify custom order." Variants:

* `{"preference": "default"}` (BackupLLMDefault)
* `{"preference": "disabled"}` (BackupLLMDisabled)
* `{"preference": "override", "order": [ ...enum values... ]}` (BackupLLMOverride — `order` is a required list of the §6.1 enum)

`prompt.cascade_timeout_seconds` (double, default 4) — "Time in seconds before cascading to backup LLM. Must be between 2 and 15 seconds."

S5 verbatim on the options: "**Default**: Uses ElevenLabs' recommended fallback sequence"; "**Custom**: Define your own cascading sequence of backup models"; "**Disabled**: No fallback (strongly discouraged for production)".

S5 verbatim warning: "Disabling backup LLMs means conversations will end abruptly if your primary LLM fails or becomes unavailable. This is strongly discouraged for production use."

S5 also advertises this at the top as a key feature, verbatim: "**High reliability**: Automatically cascade from one provider to another if one fails".

**For LetterLens, keep `backup_llm_config` at `default`, or set an explicit `override` order ending in `gemini-2.5-flash`, so a custom-LLM outage does not kill the demo.**

### 6.5 Other prompt-level knobs (S3, verbatim)

* `reasoning_effort` (enum, nullable) — "Reasoning effort of the model. Only available for some models." Allowed: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`
* `thinking_budget` (integer, nullable) — "Max number of tokens used for thinking. Use 0 to turn off if supported by the model."
* `enable_reasoning_summary` (boolean, default false) — "Enable model reasoning summaries. When disabled, we do not request summaries from provider if possible for faster TTFB. Not ZRM compatible."
* `max_tokens` (integer, default -1) — "If greater than 0, maximum number of tokens the LLM can predict"
* `ignore_default_personality` (boolean, nullable, default true) — "Whether to remove the default personality lines from the system prompt". **Note the API default is `true` but the CLI default template writes `false`** (S12) — set it explicitly.
* `timezone` (string, nullable) — verbatim: "Timezone for displaying current time in system prompt. If set, the current time will be included in the system prompt using this timezone. Must be a valid timezone name (e.g., 'America/New_York', 'Europe/London', 'UTC'). Recommended for accurate time-aware responses; without this, the agent has no knowledge of the current date/time unless you provide it via dynamic variables or tools, which can lead to incorrect or hallucinated time references." **Set this** — LetterLens deals with letters and deadlines.
* `knowledge_base` (list of KnowledgeBaseLocator), `rag` (RagConfig-Input — `enabled`, `embedding_model` (`e5_mistral_7b_instruct` | `multilingual_e5_large_instruct`), `max_vector_distance` default 0.6, `max_documents_length` default 50000, `max_retrieved_rag_chunks_count` default 20, `num_candidates`, `query_rewrite_prompt_override`)

S5 verbatim limit: "The maximum system prompt size is 2MB, which includes your agent's instructions, knowledge base content, and other system-level context."

S5 verbatim on temperature bands: "**Low (0.0-0.3)**: Deterministic, consistent responses for structured interactions"; "**Medium (0.4-0.7)**: Balanced creativity and consistency"; "**High (0.8-1.0)**: Creative, varied responses for dynamic conversations".

S5 verbatim latency warning on reasoning: "Start with a lower budget or effort for live voice agents because extra thinking can delay turn-taking."

---

## 7. First message, and starting muted / listening

### 7.1 First message — and the documented "wait for the user" behaviour (S3, verbatim)

From `AgentConfigAPIModel-Input`:

```
- `first_message` (string, optional, default: ) — If non-empty, the first message the agent will say. If empty, the agent waits for the user to start the discussion.
- `language` (string, optional, default: en) — Language of the agent - used for ASR and TTS
- `hinglish_mode` (boolean, optional, default: false) — When enabled and language is Hindi, the agent will respond in Hinglish
- `dynamic_variables` (any, optional) — Configuration for dynamic variables
- `disable_first_message_interruptions` (boolean, optional, default: false) — If true, the user will not be able to interrupt the agent while the first message is being delivered.
- `max_conversation_duration_message` (string, optional, default: ) — If non-empty, the message the agent will send when max conversation duration is reached.
- `text_behavior_overrides` (map from string to BehaviorOverride, optional, nullable) — Per-channel response behavior overrides for text conversations. Built-in channel defaults apply when unset.
- `prompt` (PromptAgentAPIModel-Input, optional) — The prompt for the agent
```

**This answers "can the agent start listening instead of speaking?" — yes, server-side: set `conversation_config.agent.first_message` to `""`.** Verbatim: "If empty, the agent waits for the user to start the discussion." Confidence: **high**.

Paired with that, `turn.initial_wait_time` (S3, verbatim): "How long the agent will wait for the user to start the conversation if the first message is empty. If not set, uses the regular turn_timeout."

So the idiomatic "start listening" config is:

```json
{
  "conversation_config": {
    "agent": { "first_message": "" },
    "turn": { "initial_wait_time": 30.0, "turn_timeout": 7.0 }
  }
}
```

Also available: `language_presets.<lang>.first_message_translation` (S3: "The translation of the first message") for multilingual first messages.

### 7.2 Overriding the first message per conversation (S15, verbatim)

```ts
const conversation = useConversation({
  overrides: {
    agent: {
      prompt: {
        prompt: "My custom prompt",
      },
      firstMessage: "My custom first message",
      language: "en",
    },
    tts: {
      voiceId: "custom voice id",
    },
    conversation: {
      textOnly: true,
    },
  },
});
```

S15 verbatim framing: "You may choose to override various settings of the conversation and set them dynamically based other user interactions."

**Gotcha:** overrides must be allowed on the agent. The CLI default template (S12) ships them **off**:

```json
"overrides": {
  "conversation_config_override": {
    "tts": { "voice_id": false },
    "conversation": { "text_only": true },
    "agent": { "first_message": false, "language": false, "prompt": { "prompt": false } }
  },
  "custom_llm_extra_body": false,
  "enable_conversation_initiation_client_data_from_webhook": false
}
```

To override `first_message` or `prompt` from the LetterLens client, flip those booleans to `true` in `platform_settings.overrides.conversation_config_override` and push. Confidence: **high** on the shape (verbatim from the shipped template); **medium** on `true` = permitted, since no page I fetched states the polarity in words — but `text_only: true` being the one pre-enabled override, alongside S3's "`overrides` … Additional overrides for the agent during conversation initiation", makes `true` = allowed the only coherent reading. Verify on first run.

### 7.3 Starting muted (client-side) (S15, verbatim)

**Controlled mic state at session start** — the React SDK takes `micMuted` as a hook option:

```ts
const [micMuted, setMicMuted] = useState(false);

const conversation = useConversation({
  micMuted,
  // ... other options
});

// Update controlled state
setMicMuted(true); // This will automatically mute the microphone
```

So **yes — the agent can start muted**: initialise `micMuted` to `true`. Confidence: **high** (verbatim snippet), though the docs do not spell out "starts muted" in words — the option is a controlled prop, so its initial value applies from the start.

Provider-level equivalent (S15, verbatim): "The provider supports `isMuted` and `onMutedChange` props for controlled mute state management, allowing you to persist mute state externally (e.g. across sessions)."

```ts
const [muted, setMuted] = useState(false);

<ConversationProvider isMuted={muted} onMutedChange={setMuted}>
```

Runtime mute controls (S15, verbatim): `useConversation()` returns "**isMuted** - whether the microphone is currently muted." and "**setMuted** - function to mute/unmute the microphone."

```ts
const { status, isSpeaking, isListening, isMuted, setMuted, canSendFeedback } = useConversation();
```

```tsx
<button onClick={() => setMuted(!isMuted)}>
  {isMuted ? 'Unmute' : 'Mute'}
</button>
```

And a dedicated hook (S15, verbatim): `useConversationInput()` — "Returns mute state and a setter for toggling the microphone."

```tsx
function MuteToggle() {
  const { isMuted, setMuted } = useConversationInput();

  return <button onClick={() => setMuted(!isMuted)}>{isMuted ? "Unmute" : "Mute"}</button>;
}
```

Starting a session (S15, verbatim): "The `startSession` method establishes the connection and starts using the microphone to communicate with the ElevenLabs Agents agent. The method accepts an options object, with `signedUrl`, `conversationToken`, or `agentId` being required." It "returns a promise resolving a `conversationId`. The value is a globally unique conversation ID you can use to identify separate conversations."

```tsx
const { startSession, endSession } = useConversationControls();
...
<button onClick={() => startSession({ agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6" })}>
```

Text-only mode (S15, verbatim): "If your agent is configured to run in text-only mode, i.e. it does not send or receive audio messages, you can use this flag to use a lighter version of the conversation. In that case, the user will not be asked for microphone permissions and no audio context will be created."

```ts
const conversation = useConversation({
  textOnly: true,
});
```

Data residency (S15, verbatim):

```ts
const conversation = useConversation({
  serverLocation: "eu-residency", // or "us", "in-residency", "global"
});
```

Widget-level mic muting also exists server-side: `platform_settings.widget.mic_muting_enabled` (default `false` in the template, S12). **Low** confidence on exact semantics — not described in prose on any page I fetched.

---

## 8. Free-tier limits for Agents

### 8.1 Free plan numbers (S16 — elevenlabs.io/pricing/agents, fetched 2026-10-03)

* **Free:** `$0per month`, "15 minutes of calls included", "4 Concurrent Calls"
* **Starter:** "75 minutes of calls included", "6 Concurrent Calls"
* **Creator:** "275 minutes of calls included", "10 Concurrent Calls"

Confidence: **medium**. This came from the marketing pricing page (ElevenLabs' own site, so primary-ish) rather than a `docs/` page, and it is the kind of number that changes. The docs route (S18) explicitly defers to it: verbatim, "For details of how many minutes are included with each subscription plan, see our [ElevenAgents pricing.](https://elevenlabs.io/pricing/agents)". **Re-check before relying on it.** I found no `docs/` page that states free-tier minutes or concurrency numerically.

**15 minutes is the single hardest constraint on the LetterLens build.** Budget demo rehearsals accordingly, and note the billing-clock warning below.

### 8.2 How calls are billed (S18, verbatim)

* "There is no cost to create your agent. The cost of calls depends on whether your agent is voice only, multimodal or text only."
* Voice only: "Voice only calls are charged based on the call duration, with a 95% discount for periods of silence longer than 10 seconds."
* **The clock gotcha, verbatim:** "The length of the call is measured based on the connection duration. This includes the time from when you begin the call, to when you end the call or the window is closed. This is why the call itself may be shorter than the duration you are charged for." → **always call `endSession()`**; a left-open tab burns the 15 minutes.
* Multimodal: "charged based on the call duration, with a 95% discount for periods of silence longer than 10 seconds. You're also charged for each text message".
* Text only: "In text only calls you're charged for each text message". Related config: `conversation.text_only` (S3, verbatim) — "If enabled audio will not be processed and only text will be used, use to avoid audio pricing."
* LLM costs: "LLM costs are passed through separately". S5 verbatim: "ElevenLabs passes through third-party LLM costs at the provider's published rate, with no markup."
* Exceeding quota, verbatim: "You need to have purchased Pay As You Go credits, or enabled usage based billing (only available on legacy subscriptions), before you can exceed your credit quota."

### 8.3 Concurrency and bursting (S17, verbatim)

* "Burst pricing allows your ElevenLabs agents to temporarily exceed your workspace's subscription concurrency limit during high-demand periods. When enabled, your agents can handle up to 3 times your normal concurrency limit, with excess calls charged at double the standard rate."
* "**Burst capacity**: Additional calls (up to a concurrency of 3x your usual limit or 300, whichever is lower) are accepted but charged at 2x the normal rate"

| Subscription limit | Burst capacity | Maximum concurrent calls |
|---|---|---|
| 10 calls | 30 calls | 30 calls |
| 50 calls | 150 calls | 150 calls |
| 100 calls | 300 calls | 300 calls |
| 200 calls | 300 calls | 300 calls (capped) |

Verbatim note: "For non-enterprise customers, the maximum burst currency can not go above 300." [typo is in the docs]

The free tier is **not** in that table — **low** confidence on whether bursting applies to a free workspace.

Per-agent knobs (S12, from the shipped template): `platform_settings.call_limits` = `{ "agent_concurrency_limit": -1, "daily_limit": 100000, "bursting_enabled": true }`. `-1` is the "no agent-level cap" sentinel. S3 lists `call_limits` (AgentCallLimits) and `queueing_config` (AgentQueueingConfig) — "Concurrency wait-queue config for the agent".

Call queueing (S19, verbatim): "When an agent or workspace reaches its concurrency limit, new calls are normally rejected immediately. With call queueing enabled, callers who arrive while the agent is at capacity are held on the line with hold audio and connected automatically, in the order they arrived, as soon as a slot frees up."

S19 verbatim on timeout: "If no slot frees up within the **Max queue wait time**, the call is disconnected. Telephony calls are hung up normally. WebSocket clients receive a `queue_status` event with status `timed_out`, followed by a close with code 4300."

S19 verbatim setting: "**Enable call queuing** | Hold callers in a queue when the agent is at its concurrency limit. | Off" (default off).

---

## 9. Things I could NOT confirm (stated plainly)

1. **No `sync` or `watch` CLI command exists.** The verbs are `init`, `add`, `status`, `push`, `pull`, `templates`, `widget embed`, `test` (S1, S11). Anything calling itself `elevenlabs agents sync` or `--watch` is invented.
2. **No verbatim JSON example of a custom-LLM agent config appears on any page I fetched.** The field names in §3 are from the API reference type listing (S3), which is authoritative for the schema, but the composed snippet in §3.3 is mine.
3. **Whether `custom_llm.url` ends at `/v1` or at `/v1/chat/completions`** — not stated verbatim anywhere I looked. Medium confidence on `/v1`.
4. **The polarity of `platform_settings.overrides.conversation_config_override.*`** (`true` = override allowed) is inferred, not quoted. Medium confidence.
5. **Free-tier minutes/concurrency come from the marketing pricing page, not docs.** Medium confidence; the docs explicitly point there rather than publishing numbers.
6. **`turn.mode: "turn"`** appears in the shipped CLI template but not in the `TurnConfig` field list captured from S3. Copy it verbatim; do not guess other values.
7. **`widget.mic_muting_enabled` semantics** — field exists in the template, no prose description found. Low confidence.
8. **"GPT-6.1 Sol"** is in the S5 prose table but has no matching enum identifier in S3. Low confidence that it is settable.
9. **`agents.json` has no `name` field** — only `config`, `id`, `branch_id`, `version_id`, `branches` (S13). How `elevenlabs agents push --agent "<agent-name>"` resolves a *name* (vs the `--agent <agent_id>` documented in S11) is unconfirmed; S8/S9 use `--agent "<agent-name>"` while S11 documents `--agent <agent_id>`. Treat as **medium** — prefer the agent ID.
10. **`FileInputConfig` internals** (`conversation.file_input`, "Configuration for file input (image/PDF uploads) during conversations") — the sub-schema was not fetched. This matters for LetterLens; worth a dedicated research pass.
11. **`VADConfig`** is listed in S3 with no fields documented on the page.

---

## 10. Recommended path for LetterLens (synthesis, not quoted)

1. `npx @elevenlabs/cli agents init` (or `scoop install elevenlabs` on this Windows box), then `elevenlabs generate-skills` so the repo carries version-matched CLI docs offline.
2. `elevenlabs auth login` locally; `ELEVENLABS_API_KEY` in `.env` for scripts/CI.
3. `elevenlabs agents add "LetterLens" --template minimal` → edit `agent_configs/letterlens.json` → `elevenlabs agents push --dry-run` → `push`.
4. Create tools separately (`elevenlabs tools add ... --type webhook|client`) and reference the returned IDs in `conversation_config.agent.prompt.tool_ids`. **Never** use `prompt.tools`.
5. Primary LLM: `custom-llm` with `temperature: null` and `api_key: {"secret_id": ...}`. Keep `backup_llm_config` at `{"preference": "default"}` so a custom-LLM failure cascades instead of ending the call.
6. Set `agent.timezone`, `asr.keywords` (letter/benefit domain terms), and `first_message: ""` + `turn.initial_wait_time` if LetterLens should listen first.
7. Flip the `platform_settings.overrides.conversation_config_override` booleans you need **before** relying on client-side overrides.
8. Guard the 15 free minutes: always `endSession()`, use `conversation.text_only` for non-voice testing, and drop `max_duration_seconds` from 600 during development.

---

## Independent verification (adversarial pass)

**Verification date:** 2026-10-03
**Method:** every page below was re-fetched from scratch in this pass (raw `curl`, not from memory and not trusting the researcher's citations). Raw copies were diffed against the claims field-by-field. Where a claim's cited URL did not in fact contain the fact, that is recorded as a **misattributed citation** even when the fact itself checks out elsewhere.

Pages re-fetched independently (all HTTP 200, 2026-10-03):

| Ref | URL | Bytes |
|---|---|---|
| V1 | https://elevenlabs.io/docs/eleven-agents/operate/cli.md | 8436 |
| V2 | https://raw.githubusercontent.com/elevenlabs/cli/main/README.md | 17676 |
| V3 | https://raw.githubusercontent.com/elevenlabs/cli/main/cli/elevenlabs/workflow/project.rs | 26388 |
| V4 | https://raw.githubusercontent.com/elevenlabs/cli/main/cli/elevenlabs/workflow/templates.rs | 14358 |
| V5 | https://elevenlabs.io/docs/api-reference/agents/create.md | 177521 |
| V6 | https://elevenlabs.io/docs/api-reference/tools/create.md | 56933 |
| V7 | https://elevenlabs.io/docs/eleven-agents/customization/llm.md | 11941 |
| V8 | https://elevenlabs.io/docs/eleven-agents/customization/llm/custom-llm.md | 30036 |
| V9 | https://elevenlabs.io/docs/api-reference/authentication.md | 2161 |
| V10 | https://elevenlabs.io/docs/eleven-agents/libraries/react.md | 21284 |
| V11 | https://elevenlabs.io/docs/help-center/product/eleven-agents/how-much-does-eleven-agents-cost.md | 2851 |
| V12 | https://elevenlabs.io/docs/eleven-agents/customization/tools/webhook-tools.md | 20741 |
| V13 | https://api.elevenlabs.io/openapi.json | 2252803 |
| V14 | https://registry.npmjs.org/@elevenlabs/cli/latest | — |
| V15 | https://elevenlabs.io/pricing/agents | 715361 |
| V16 | https://elevenlabs.io/docs/eleven-agents/guides/burst-pricing.md | — |
| V17 | https://elevenlabs.io/docs/api-reference/agents/create (HTML) | — |

### Verdict table

| # | Claim | Status |
|---|---|---|
| 1 | CLI npm package / installs | **CONFIRMED** |
| 2 | npm 1.4.0, bin, v0→v1 breaking change | **CONFIRMED** |
| 3 | Command surface; no `sync`, no `watch` | **CONFIRMED** |
| 4 | On-disk layout | **CONFIRMED** |
| 5 | `agents.json` / `tools.json` schema; no `name` field | **CONFIRMED** |
| 6 | Configs are the REST wire body verbatim | **CONFIRMED** |
| 7 | `DEFAULT_TEMPLATE_JSON` + six templates | **CONFIRMED** (byte-for-byte) |
| 8 | `prompt.tools` deprecated, use `tool_ids` | **CONFIRMED** |
| 9 | `POST /v1/convai/tools`, body, flow | **CONFIRMED** (citation misattributed) |
| 10 | Unwrapped CLI file vs wrapped REST body; timeouts | **CONFIRMED** |
| 11 | `llm: "custom-llm"` + `CustomLLM` object | **CONFIRMED** |
| 12 | `temperature: null` for custom LLMs | **CONFIRMED** |
| 13 | Custom-LLM SSE contract | **CONFIRMED with a correction** (Responses API chunk format is different) |
| 14 | `POST /v1/convai/agents/create` shape | **CONFIRMED** |
| 15 | `xi-api-key` header; spec artefact; curl omits it | **CONFIRMED** (all three parts) |
| 16 | Empty `first_message` + `turn.initial_wait_time` | **CONFIRMED** |
| 17 | React SDK mute surface | **CONFIRMED** |
| 18 | Overrides must be opted into | **CONFIRMED, and the inferred polarity is now PROVEN** |
| 19 | "The **complete** `prompt.llm` enum" | **REFUTED as worded** — every ID listed is real, but the list is a ~15% subset of a ~110-value enum |
| 20 | `backup_llm_config` / `cascade_timeout_seconds` | **CONFIRMED** (field names are on V5, not on the cited V7) |
| 21 | Free 15 min / 4 concurrent; Starter 75/6; Creator 275/10 | **CONFIRMED** |
| 22 | Billing on connection duration | **CONFIRMED** (one nuance omitted) |
| 23 | `elevenlabs generate-skills` | **CONFIRMED** (verbatim) |
| 24 | `conversation.file_input` exists, sub-schema unconfirmed | **First half CONFIRMED; second half REFUTED — the sub-schema IS on the same page the researcher cited** |

### Claim-by-claim notes

**1, 4, 23 — CONFIRMED verbatim from V1.** V1 says, word for word: "Homebrew (macOS) and Scoop (Windows) are the recommended install methods and ship a standalone binary." and "After installation, the `elevenlabs` command will be available globally in your terminal." The `generate-skills` tip in §2.2 of this note is reproduced exactly. Project tree matches exactly.
*Small addition V1 makes that §2.3 of this note omits:* `elevenlabs auth login` — "This will open up a browser window to authenticate via OAuth. The CLI will verify the credentials and store them securely." So interactive login is OAuth, not key-paste. V2 separately documents the key path (`ELEVENLABS_API_KEY`, `.env`, or `--xi-api-key xi-...` per command).

**2 — CONFIRMED.** V14 returned verbatim:
```json
{"name":"@elevenlabs/cli","version":"1.4.0","description":"CLI for elevenlabs","bin":{"elevenlabs":"bin/cli.js"}}
```
The v0→v1 migration note in V2 matches the quote in §2.1 word for word. Note the version is *not* in the README — it is only in the registry, so it will drift.

**3 — CONFIRMED.** The command block in §2.4 of this note is a byte-for-byte copy of V2's. Grepping V2 and V1 for `watch` returns nothing at all, and every `sync`/`Sync` hit is prose ("push/pull sync", "Sync configs with ElevenLabs", "syncing them with ElevenLabs") or the V1 heading "Synchronization" — never a command. **No `agents sync`, no `--watch`, no `agents watch`. Confirmed.**

**5 — CONFIRMED.** V3 matches the struct listing in §2.6 exactly, including `#[serde(rename = "type")]` on `ToolDefinition` and `skip_serializing_if = "Option::is_none"` on every optional. **There is no `name` field on an `agents.json` entry — confirmed.** V3's doc comment also states the design intent verbatim: "Entity **configs** are stored as raw wire JSON (`serde_json::Value`) and pushed verbatim, so they round-trip losslessly" and "Their `config` field is a *path*, not an inline config."

**6 — CONFIRMED verbatim from V2:** "agent configs live as JSON on disk and sync to ElevenLabs. Pulled configs are stored as raw wire JSON and pushed back verbatim, so they round-trip losslessly." The inference that the Create-agent API reference is therefore the authoritative schema for `agent_configs/*.json` is sound — with one caveat, see "`turn.mode`" below.

**7 — CONFIRMED byte-for-byte.** `DEFAULT_TEMPLATE_JSON` in V4 is identical to §2.8 of this note, including `turn: {turn_timeout: 7.0, silence_end_call_timeout: -1.0, mode: "turn"}`, `asr.provider: "scribe_realtime"`, `agent.first_message: ""`, `prompt.llm: "gemini-2.5-flash"`, `prompt.tool_ids: []`, `prompt.custom_llm: null`, `tts.voice_id: "cjVigY5qzO86Huf0OWal"`, `tts.model_id: "eleven_flash_v2"`. `TEMPLATE_OPTIONS` holds exactly six entries and `template_by_name` matches on exactly those six.

**8 — CONFIRMED verbatim from V5** (`PromptAgentAPIModel-Input`):
```
- `tool_ids` (list of string, optional) — A list of IDs of tools used by the agent
- `tools` (list of PromptAgentApiModelInputToolsItems, optional, deprecated) — A list of tools that the agent can use over the course of the conversation, use tool_ids instead
```

**9 — CONFIRMED, citation misattributed.** The flow quote is genuinely on V12, verbatim: "Edit `agent_configs/<agent-name>.json` and add the tool's ID to `conversation_config.agent.prompt.tool_ids`, then push:" followed by `elevenlabs agents push --agent "<agent-name>"`. But the endpoint, the "Add a new tool to the available tools in the workspace" description, the `{tool_config, response_mocks}` body and the `id` in the response are **not on V12 at all** — they are on V6. Both verified; cite V6 for the wire shape.

**10 — CONFIRMED on both halves.** V12 shows the CLI file unwrapped (`type`/`name`/`description`/`api_schema` at top level of `tool_configs/get_weather.json`) and the API call wrapping the identical object in `tool_config`/`toolConfig` — on the same page, a few lines apart. V6 confirms both ranges verbatim:
* webhook — `response_timeout_secs` (integer, optional, default: 20) — "Must be between 5 and 300 seconds (inclusive)."
* client — `response_timeout_secs` (integer, optional, default: 20) — "Must be between 1 and 120 seconds (inclusive)."

**11 — CONFIRMED verbatim from V5.** Every field, type, nullability, default and enum value in §3.2 matches `### CustomLLM` exactly. `custom-llm` is present in the `llm` enum. `CustomLlmApiKey` has its own stub type carrying only the description — i.e. **the docs never show the concrete shape of the key object anywhere**, only the prose `{'secret_id': '...'}` / `{'env_var_label': '...'}`. The researcher's gotcha stands and is correctly flagged.

**12 — CONFIRMED verbatim from V5:** "`temperature` (double, optional, nullable, default: 0) — The temperature for the LLM. Defaults to 0. Set to null to omit the parameter from the LLM request entirely (useful for custom LLMs that reject the temperature field)."

**13 — CONFIRMED with a correction that will break a Responses-API build.** V8 verbatim: "Both endpoints must return responses in SSE (Server-Sent Events) format with `Content-Type: text/event-stream`." and, for Chat Completions, "Each chunk must be formatted as `data: {json}\n\n` and the stream must end with `data: [DONE]\n\n`."
**The claim then wrongly generalises that chunk format to both endpoints.** V8's Responses API section says something different, verbatim:
> "Each chunk must be formatted as `event: {type}\ndata: {json}\n\n` and the stream must end with `data: [DONE]\n\n`. The minimum required events are:
> * `response.output_text.delta` - for streaming text content
> * `response.completed` - to signal completion"

So: `data: {json}\n\n` is Chat-Completions-only; the Responses API needs a named `event:` line per chunk plus those two event types. Only `data: [DONE]\n\n` is shared.

**14 — CONFIRMED verbatim from V5** — endpoint, `Content-Type: application/json`, the five residency servers, `conversation_config` as the only required body field, the three optional siblings plus `name`/`tags`, `200 → {agent_id}`, `422 → detail`, and `enable_versioning` (boolean, optional, default: true, deprecated) — "Deprecated: all agents are versioned. This parameter is ignored."

**15 — CONFIRMED on all three parts, including the one that sounded like a guess.** V9 verbatim: "All API requests should include your API key in an `xi-api-key` HTTP header as follows:" / `xi-api-key: ELEVENLABS_API_KEY`, and "Every request to the API must include your API key". V13 (live spec, fetched and parsed in this pass) confirms on `/v1/convai/agents/create` POST:
```json
{"name":"xi-api-key","in":"header","required":false,"schema":{"anyOf":[{"type":"string"},{"type":"null"}],"description":"Your API key. This is required by most endpoints to access our API programmatically. You can view your xi-api-key using the 'Profile' tab on the website."}}
```
and `components.securitySchemes` is **absent** and top-level `security` is **null**. V17 (the rendered HTML) confirms the displayed curl sample verbatim and it does indeed omit the header:
```bash
curl -X POST https://api.elevenlabs.io/v1/convai/agents/create \
     -H "Content-Type: application/json" \
     -d '{
  "conversation_config": {}
}'
```
*Nuance worth knowing:* the HTML page's **Headers** panel does list `xi-api-key`, and the generated per-language snippets in the "Try it" panel **do** send it (e.g. Go `req.Header.Add("xi-api-key", "string")`, Ruby `request["xi-api-key"] = 'string'`). Only the top curl sample drops it. Also: the `.md` rendering's `## Examples` block shows the request body as `{}`, not `{"conversation_config": {}}` — two different renderings of the same operation. **Always send the header.**

**16 — CONFIRMED verbatim from V5.** `first_message` (string, optional, default: ) — "If non-empty, the first message the agent will say. If empty, the agent waits for the user to start the discussion." and `initial_wait_time` (double, optional, nullable) — "How long the agent will wait for the user to start the conversation if the first message is empty. If not set, uses the regular turn_timeout."
*Related field the note missed:* `disable_first_message_interruptions` (boolean, default false) — "If true, the user will not be able to interrupt the agent while the first message is being delivered."

**17 — CONFIRMED verbatim from V10**, all four parts:
* `useConversation({ micMuted })` under "Controlled State", with the comment `setMicMuted(true); // This will automatically mute the microphone`
* "The provider supports `isMuted` and `onMutedChange` props for controlled mute state management, allowing you to persist mute state externally (e.g. across sessions)." → `<ConversationProvider isMuted={muted} onMutedChange={setMuted}>`
* `useConversation()` returns `isMuted` ("whether the microphone is currently muted") and `setMuted` ("function to mute/unmute the microphone")
* `useConversationInput()` → `const { isMuted, setMuted } = useConversationInput();`

**18 — CONFIRMED, and the polarity the researcher flagged as "inferred, not quoted" is now PROVEN.** V10 confirms the client-side override surface verbatim: `overrides: { agent: { prompt: { prompt }, firstMessage, language }, tts: { voiceId }, conversation: { textOnly } }`. V5 settles the polarity — every boolean in the override-permission schemas is described as "**Whether to allow** overriding the X field" with **default: false**:
```
### AgentConfigOverrideConfig
- `first_message` (boolean, optional, default: false) — Whether to allow overriding the first_message field.
- `language` (boolean, optional, default: false) — Whether to allow overriding the language field.
- `max_conversation_duration_message` (boolean, optional, default: false) — ...
- `prompt` (PromptAgentAPIModelOverrideConfig, optional) — Configures overrides for nested fields.

### PromptAgentAPIModelOverrideConfig
- `prompt` (boolean, optional, default: false) — Whether to allow overriding the prompt field.
- `llm` (boolean, optional, default: false) — Whether to allow overriding the llm field.
- `tool_ids` (boolean, optional, default: false) — Whether to allow overriding the tool_ids field.
- `native_mcp_server_ids` (boolean, optional, default: false) — ...
- `knowledge_base` (boolean, optional, default: false) — ...

### ConversationConfigOverrideConfig
- `text_only` (boolean, optional, default: false) — Whether to allow overriding the text_only field.
- `max_duration_seconds` (boolean, optional, default: false) — Whether to allow overriding the max_duration_seconds field.

### TTSConversationalConfigOverrideConfig
- `model_id` / `voice_id` / `supported_voices` / `stability` / `speed` (boolean, optional, default: false each)

### ASRConversationalConfigOverrideConfig
- `keywords` (boolean, optional, default: false) — Whether to allow overriding the keywords field.
```
**`true` = allowed. Confirmed, not inferred.** More overridables exist than the shipped template writes: `prompt.llm`, `prompt.tool_ids`, `prompt.knowledge_base`, `tts.model_id`, `tts.stability`, `tts.speed`, `conversation.max_duration_seconds`, `asr.keywords`, `agent.max_conversation_duration_message`. Also note `ConversationInitiationClientDataConfig-Input` carries two further gates the note does not mention: `enable_starting_workflow_node_id_from_client` and `enable_procedure_ids_from_client`, both default false — "if false, sending it fails conversation start."

**19 — REFUTED AS WORDED. Read this one before writing any `llm` value.**
Good news first: **every one of the 16 model IDs the researcher listed is real and present in the enum on V5** — `gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-3.8-flash`, `gpt-5.6-sol`, `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`, `claude-opus-5`, `claude-opus-5-5`, `claude-sonnet-5`, `claude-haiku-4-5`, `deepseek-v41-flash`, `glm-52`, `qwen36-35b-a3b`, `qwen35-397b-a17b`, `custom-llm`. None is hallucinated. And the `gpt-6.1-sol` catch is correct and verified: V7's prose table lists "GPT-6.1 Sol" under OpenAI while **no `gpt-6.1-sol` appears anywhere in the enum on V5** — a real docs inconsistency; trusting the enum is the right call.
The word **"complete" is wrong**, and dangerously so: the actual enum holds roughly 110 values. Anything built on "the enum is these 16" (a validator, a dropdown, a TS union) will reject valid models. Models in the enum that the researcher's list omits include: `gpt-5.5`, `gpt-5.6-terra`, `gpt-5.6-luna`, `gpt-5.4`/`-mini`/`-nano`, `gpt-5.2`, `gpt-5.2-chat-latest`, `gpt-5.1`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-4.1`/`-mini`/`-nano`, `gpt-4o`, `gpt-4o-mini`, `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`, `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite`, `gemini-3.1-flash-lite-preview`, `gemini-3-pro-preview`, `gemini-3-flash-preview`, `gemini-2.5-flash-lite`, `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-pro`, `gemini-1.5-flash`, `claude-sonnet-5-5`, `claude-sonnet-4-6`, `claude-sonnet-4-5`, `claude-sonnet-4`, `claude-opus-4-8`, `claude-opus-4-7`, `claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-sonnet-v1`, `claude-3-haiku`, `grok-beta`, `qwen3-4b`, `qwen3-30b-a3b`, `gpt-oss-20b`, `gpt-oss-120b`, `glm-45-air-fp8`, `watt-tool-8b`, `watt-tool-70b`, plus ~30 pinned/dated variants (`gpt-5.4-2026-03-05`, `claude-sonnet-4-5@20250929`, `gemini-2.5-flash-preview-09-2025`, …).
**Treat `prompt.llm` as an open string validated server-side, and re-read the enum on V5 before hardcoding a set.** The identical enum is reused in three other places on V5: `PromptEvaluationCriteria.llm`, `BackupLLMOverride.order`, and the workflow-override variants.

**20 — CONFIRMED, but the field names are not on the cited page.** V7 (the cited page) carries only the prose and the warning. The warning is verbatim: "Disabling backup LLMs means conversations will end abruptly if your primary LLM fails or becomes unavailable. This is strongly discouraged for production use." and the three options as prose: "**Default**: Uses ElevenLabs' recommended fallback sequence / **Custom**: Define your own cascading sequence of backup models / **Disabled**: No fallback (strongly discouraged for production)". **V7 contains neither `backup_llm_config` nor `cascade_timeout_seconds` nor `preference` anywhere.** Those are on V5, verbatim:
```
### PromptAgentApiModelInputBackupLlmConfig
Configuration for backup LLM cascading. Can be disabled, use system defaults, or specify custom order.
- `preference`: `default` (BackupLLMDefault)
- `preference`: `disabled` (BackupLLMDisabled)
- `preference`: `override` (BackupLLMOverride)
  - `order` (list of enum, required)
```
and `cascade_timeout_seconds` (double, optional, default: 4) — "Time in seconds before cascading to backup LLM. Must be between 2 and 15 seconds." The discriminator values are the API's (`override`), not the UI's ("Custom") — don't send `"custom"`. Cite V5. A page neither pass has read exists at `/docs/eleven-agents/customization/llm/llm-cascading`.

**21 — CONFIRMED from V15.** The page renders: Free `$0` / "15 minutes" / "4 Concurrent Calls"; Starter "75 minutes" / "6 Concurrent Calls"; Creator `$22` / "275 minutes" / "10 Concurrent Calls". V11 does defer, verbatim: "For details of how many minutes are included with each subscription plan, see our [ElevenAgents pricing.]" — so the researcher's "no docs page publishes these numerically" is right.
V15 publishes more than the note captured, in a FAQ paragraph worth having verbatim: "Included call minutes and concurrent calls per plan: Free 15 minutes / 4 concurrent calls; Starter 75 minutes / 6; Creator 275 minutes / 10; Pro 1,238 minutes / 20; Scale 3,738 minutes / 30; Business 12,375 minutes / 40. Additional call minutes cost $0.08 per minute (burst pricing $0.16 per minute, double the standard rate, when you exceed your concurrency limit), and text messages cost $0.003 each. LLM usage is billed separately on top, based on the model you choose."
**$0.003 per text message is the number that makes the text-only dev-loop mitigation concrete** — ~333 messages per dollar versus 15 total voice minutes.

**22 — CONFIRMED verbatim from V11**, with the exact sentence slightly longer than quoted: "The length of the call is measured based on the connection duration. This includes the time from when you begin the call, to when you end the call or the window is closed. This is why the call itself may be shorter than the duration you are charged for." Also verbatim: "There is no cost to create your agent." and "Voice only calls are charged based on the call duration, with a 95% discount for periods of silence longer than 10 seconds."
*Two nuances the note flattens.* (a) The 95% silence discount is documented for **voice-only and multimodal**; text-only has no duration component at all. (b) "no markup" is on V7, not V11, and V7 qualifies it: "ElevenLabs passes through third-party LLM costs at the provider's published rate, with no markup. Select Gemini and Claude models are aligned with Vertex AI regional (non-global) pricing, which is what US and EU traffic is billed at — **a 10% increase on input, output, and cache tokens**, matching Vertex regional rates." So LLM pass-through is not strictly at list price for Gemini/Claude on US/EU traffic.
*Also:* V5 has `turn.retranscribe_on_turn_timeout` — "Disables silence discount billing for affected turns." Leaving it off protects the 95% discount.

**23 — CONFIRMED verbatim from V1.** The quote in §2.2 is exact, including `--output-dir`.

**24 — Half confirmed, half refuted, and the refuted half is this pass's biggest win.**
`conversation.file_input` exists exactly as quoted on V5: "`file_input` (FileInputConfig, optional) — Configuration for file input (image/PDF uploads) during conversations." **But the claim that "the FileInputConfig sub-schema was NOT fetched and its fields are unconfirmed" is wrong — the sub-schema is on V5, the very page cited, about 280 lines above the field itself.** Verbatim:
```
### FileInputConfig

- `enabled` (boolean, optional, default: true) — When enabled, users may attach images or PDFs in chat when the LLM supports multimodal input.
- `max_files_in_memory` (integer, optional, default: 10) — Number of most-recent files kept in memory during a conversation. Older files are summarized and their bytes freed.
- `max_files_per_conversation` (integer, optional, default: 10) — Total files a user can upload in one conversation. Uploads are billed per file. Use -1 for no limit, or a value >= max_files_in_memory.
```
Three things in there change the LetterLens design:
1. **`enabled` defaults to `true`** — file input is on out of the box; no flag to flip to accept a letter.
2. **"when the LLM supports multimodal input"** — the upload path is gated on the model. The CLI default `gemini-2.5-flash` is multimodal, but `prompt.llm` and letter-image support are now coupled: swapping to a text-only model silently kills the core feature. No doc page fetched in either pass lists which enum values are multimodal — **this is the one real remaining gap.**
3. **"Uploads are billed per file"** — a third billing axis beyond minutes and messages, and unpriced on V15. Budget for it.
V5 also shows a `FileInputConfigWorkflowOverride` type, so file input can be varied per workflow node.
*Corroborating evidence the note missed:* `WidgetTextContents` on V5 has a full set of upload strings — `attach_file`, `remove_file`, `file_upload_error`, `file_type_unsupported` ("Followed by the list of accepted types"), `file_too_large`, `file_limit_reached` — so the shipped widget has a real file-attach UI, not just an API field.

### Things the researcher missed that the build will need

1. **`FileInputConfig` is fully documented.** See claim 24 above. This was logged as a blocker needing "its own research pass"; it does not.
2. **Override polarity is proven, not inferred.** `true` = allowed, default `false`. The blocker that said "verify on first run" can be closed. See claim 18.
3. **`turn.mode` is not a documented field.** The shipped `DEFAULT_TEMPLATE_JSON` writes `"mode": "turn"` inside `turn`, but `TurnConfig` on V5 has no `mode`. What it does have is `turn_model` (enum, default `turn_v3`, allowed `turn_v2`/`turn_v3`). Since configs are pushed as raw wire JSON, an unmodeled key rides along; it is probably ignored, but if a push ever 422s on `turn`, drop `mode` first. Do not invent values for it.
4. **Four tool types, not two.** `ToolRequestModelToolConfig` on V6 is a union over `type`: **`client`, `mcp`, `system`, `webhook`.** The CLI's `tools.json` only tracks `webhook`/`client` (V3), so `system` tools (end call, language detection, transfer, skip turn, voicemail detection) and `mcp` are API-only — they cannot be registered through `elevenlabs tools add`.
5. **Evaluation criteria must be objects, and bare strings return 500.** V4 carries this comment verbatim above the customer-service template: *"PromptEvaluationCriteria objects, not bare strings: `id`, `name` and `conversation_goal_prompt` are all required, and a list of strings makes the create endpoint return 500."* V5 confirms all three are required. A 500 (not a 422) means no useful validation message.
6. **The `text-only` template flips a third field.** §2.9 lists only `conversation.text_only = true` and `widget.supports_text_only = true`. V4 also sets `platform_settings.overrides.conversation_config_override.conversation.text_only = false` — i.e. the text-only template **revokes** the client's ability to override text-only, the one override the default template grants. There is a unit test in V4 asserting exactly this (`text_only_flips_conversation_flag`). Matters for LetterLens: if the plan is "text-only for dev, client flips to voice", starting from the `text-only` template blocks it; start from `default`.
7. **`tests.json` and the whole `elevenlabs tests` group are undocumented in the note.** V3: `TestsConfig { tests: Vec<TestDefinition> }`, `TestDefinition { config: String, type: Option<String>, id: Option<String> }`. V2 documents `tests add <name> [--template basic-llm|tool|conversation-flow|customer-service]`, `tests templates list`, `tests push`/`pull`/`delete`, attachment via `platform_settings.testing.attached_tests`, and auto-discovery: `tests push` "scans `--config-dir` recursively for `.json` files that look like tests (a `chat_history` array or a `success_condition` string) and registers them in `tests.json` before pushing." **This is the cheapest way to regression-test agent logic without burning voice minutes.**
8. **Reasoning controls exist on `prompt` and default off.** V5: `reasoning_effort` (enum, nullable; `none`/`minimal`/`low`/`medium`/`high`/`xhigh`/`max`), `thinking_budget` (integer, nullable; "Use 0 to turn off"), `enable_reasoning_summary` (boolean, default false; "Not ZRM compatible"). V7 warns: "Start with a lower budget or effort for live voice agents because extra thinking can delay turn-taking."
9. **`built_in_tools` and `enable_parallel_tool_calls` are separate from `tool_ids`.** V5: `built_in_tools` (BuiltInTools-Input) — "Built-in system tools to be used by the agent", and `enable_parallel_tool_calls` (boolean, **default true**) — "Not supported by all models." System tools do not need a `POST /v1/convai/tools` round trip.
10. **Max system prompt size is 2MB** (V7, verbatim): "The maximum system prompt size is 2MB, which includes your agent's instructions, knowledge base content, and other system-level context."
11. **Turn-detection fields the note's §2.11 omits** (all V5): `speculative_turn` (default false) — "starts generating LLM responses during silence before full turn confidence is reached, reducing perceived latency. May increase LLM costs."; `retranscribe_on_turn_timeout` (default false, kills the silence discount); `turn_model` (default `turn_v3`); `interruption_ignore_terms` + `interruption_ignore_term_languages` + `merge_with_default_ignore_terms`; `transcribe_on_disabled_interruptions`; `soft_timeout_config` — "Provides immediate feedback during longer LLM responses" (useful while a letter is being read).
12. **Agent-level fields the note omits** (V5 `AgentConfigAPIModel-Input`): `disable_first_message_interruptions`, `max_conversation_duration_message` ("the message the agent will send when max conversation duration is reached" — pair this with a lowered `max_duration_seconds` so the dev cap is not a silent cut-off), `hinglish_mode`, `text_behavior_overrides`.
13. **Burst pricing is documented and resolves the open blocker.** V16: bursting gives "up to 3 times your normal concurrency limit, with excess calls charged at double the standard rate", capped — "For non-enterprise customers, the maximum burst currency can not go above 300" — burst calls are "deprioritized… for speech-to-text and text-to-speech processing", and over-capacity calls are "rejected with an error, unless call queueing is enabled". It is set per agent at `platform_settings.call_limits.bursting_enabled`, which **the shipped default template sets to `true`**. V15's per-minute table does carry a "Free / Pay as you go" column with a burst row at `$0.160`, so bursting is priced for free/PAYG; with a 4-call concurrency limit it is near-irrelevant for LetterLens, but **`bursting_enabled: true` in the template means a runaway client could burst to 12 concurrent calls at 2x rate.** Consider setting it `false` for a hackathon agent.
14. **`optimize_streaming_latency` deprecation re-confirmed.** V5: "Deprecated: this field is a no-op and is ignored." V4 still writes `3`. Harmless, but it means **the shipped template is not clean against the current schema** — a second reason (with `turn.mode`) not to treat `DEFAULT_TEMPLATE_JSON` as schema-authoritative. Prefer `minimal` plus explicit fields.
15. **`ignore_default_personality` really does disagree.** V5: "(boolean, optional, nullable, **default: true**) — Whether to remove the default personality lines from the system prompt." V4 writes `false`. Confirmed divergence — set it explicitly.
16. **`prompt.timezone` is real and the warning is verbatim** (V5): "Timezone for displaying current time in system prompt. If set, the current time will be included in the system prompt using this timezone. Must be a valid timezone name (e.g., 'America/New_York', 'Europe/London', 'UTC'). Recommended for accurate time-aware responses; without this, the agent has no knowledge of the current date/time unless you provide it via dynamic variables or tools, which can lead to incorrect or hallucinated time references." The blocker is well-founded; `timezone` is not in the shipped template, so it must be added by hand.
17. **CLI conveniences not in the note** (V2): `elevenlabs residency <region>` (persisted in `~/.elevenlabs/config.json`, applies to every command); `--dry-run` is a **global** flag on every operation, not just `agents push` ("Validate the request locally and print the HTTP request without sending it"); `--json <JSON|->`, `--params`, `--format json|table|yaml|csv`, `--page-all`; `elevenlabs components add <name>` for ElevenLabs UI; `elevenlabs say`; `elevenlabs completion <shell>`; and a full command reference at `./reference.md` in the repo. Also `--intent` sends an `X-Agent-Intent` header and **drops values containing credentials or absolute paths** — fine, but do not put letter content in it.
18. **Pages neither pass has read, in rough priority order:** `/docs/eleven-agents/customization/llm/llm-cascading` (the backup-LLM mechanics behind claim 20), `/docs/eleven-agents/operate/hosted-mcp` (agent management with no install), `/docs/eleven-agents/guides/call-queueing`, `/docs/eleven-agents/customization/privacy/zrm`, `/docs/api-reference/tokens/create` (single-use tokens — the right way to start a conversation from LetterLens's browser client without shipping `xi-api-key`), and `/docs/eleven-agents/customization/llm/optimizing-costs`.

### Net assessment

This is an unusually accurate research pass. Of 24 claims, 22 hold exactly as written, and every verbatim JSON block, field name, enum value and quoted sentence I re-fetched matched character for character — including the two that most looked like model-family hallucinations (`gpt-6-astra`/`claude-opus-5`/`glm-52` are all genuinely in the enum, and the `gpt-6.1-sol` docs-vs-enum inconsistency is a real find). **No hallucinated package name, no hallucinated endpoint, no hallucinated field, and no capability asserted beyond what the docs grant.** The researcher's habit of flagging its own uncertainty (`turn.mode`, the override polarity, the custom-LLM `url` suffix) pointed straight at the two genuinely soft spots.

Two defects matter before code is written. **Claim 19's word "complete" is the dangerous one** — the real `prompt.llm` enum is ~110 values, not 16, so any validator or type built from that list rejects valid models; treat `llm` as an open string. **Claim 13 generalises the Chat Completions SSE chunk format to the Responses API, which uses `event: {type}\ndata: {json}\n\n` instead** — that would silently break a `/v1/responses` custom-LLM server. Everything else is citation hygiene: claims 9 and 20 are true but sourced to pages that do not contain them (use `tools/create.md` and `agents/create.md` respectively).

Against the stated blockers: nine of eleven are confirmed and well-founded. Two can now be closed — **override polarity is documented (`true` = allowed, default `false`)**, and **`FileInputConfig` is not an open gap; it was on the page already cited**. The residual unknown is narrower and sharper than the blocker list suggests: not "how do letters reach the agent", but **which `prompt.llm` values satisfy "when the LLM supports multimodal input"** — no page fetched in either pass answers that, and the whole product depends on it. Add to that two newly surfaced build facts: **uploads are billed per file** (a third billing axis, unpriced anywhere) and **text messages cost $0.003 each**, which is what makes the text-only dev loop the correct mitigation for a 15-minute voice budget.
