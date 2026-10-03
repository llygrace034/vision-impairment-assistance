# LetterLens Research 04 — ElevenLabs Browser/React SDK for Agents (WebRTC/WebSocket voice session)

Researched: 2026-10-03. Every fact below was fetched in-task from a primary source. Each section
names its source. Where the published docs page and the published package's own TypeScript
definitions disagree, both are recorded and the disagreement is flagged — the `.d.ts` shipped in the
npm tarball is treated as authoritative for API shape, because that is what the compiler enforces.

Sources used (all fetched 2026-10-03):

| # | Source | URL |
|---|---|---|
| S1 | Docs index | https://elevenlabs.io/docs/llms.txt |
| S2 | React SDK docs | https://elevenlabs.io/docs/eleven-agents/libraries/react.md |
| S3 | JavaScript SDK docs | https://elevenlabs.io/docs/eleven-agents/libraries/java-script.md |
| S4 | Client tools | https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools.md |
| S5 | Dynamic variables | https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables.md |
| S6 | Authentication | https://elevenlabs.io/docs/eleven-agents/customization/authentication.md |
| S7 | Client events | https://elevenlabs.io/docs/eleven-agents/customization/events/client-events.md |
| S8 | Conversation flow (interruptions/turn-taking) | https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow.md |
| S9 | Get conversation token (API ref) | https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-webrtc-token.md |
| S10 | Get signed URL (API ref) | https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-signed-url.md |
| S11 | Next.js quickstart | https://elevenlabs.io/docs/eleven-agents/guides/quickstarts/next-js.md |
| S12 | npm registry metadata | https://registry.npmjs.org/@elevenlabs%2Freact (and sibling packages) |
| S13 | Published type definitions | https://cdn.jsdelivr.net/npm/@elevenlabs/react@1.16.0/dist/… and https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.26.0/dist/… |
| S14 | Package README | https://cdn.jsdelivr.net/npm/@elevenlabs/react@1.16.0/README.md |

---

## 0. TL;DR for the LetterLens build

- Install **`@elevenlabs/react`** (latest **1.16.0**). It re-exports all of `@elevenlabs/client`
  (`export * from "@elevenlabs/client";`), so you do **not** need to add `@elevenlabs/client`
  separately for a React app.
- The **modern API is provider-based**: wrap in `<ConversationProvider>`, then use
  `useConversationControls()` / `useConversationStatus()` / `useConversationMode()`, or the
  convenience `useConversation()`.
- **`startSession` in the React SDK returns `void`** — it is fire-and-forget. Do **not** `await` it
  for a conversation id. Get the id from `onConnect({ conversationId })` or `getId()`.
- Connection type is **auto-inferred**: voice → WebRTC, text-only → WebSocket. Do not hardcode it.
- For a **public** agent: `startSession({ agentId })`. For a **private** agent (`enable_auth` on):
  mint a **conversation token** server-side (`GET /v1/convai/conversation/token?agent_id=...` with
  `xi-api-key`) and pass `conversationToken` → WebRTC. The signed-URL path
  (`get-signed-url` → `signedUrl`) is the WebSocket equivalent and still supported.
- **Barge-in is server-driven, not client-logic.** The SDK handles the `interruption` event by
  flushing output audio. But per S8 the `interruption` client event must be **enabled on the agent**
  in the dashboard, otherwise interruptions will not take effect.
- Live transcript: `onMessage` fires with `{ message, event_id, role, source }`. `source` is
  `"user" | "ai"` and is **marked `@deprecated`** in favour of `role: "user" | "agent"`.
  Use `role`.

---

## 1. Package names — current vs deprecated, with versions

Source: S12 (npm registry), S2, S3, S14.

### Current (use these)

| Package | `latest` | `next` | Publish date of latest | Notes |
|---|---|---|---|---|
| `@elevenlabs/react` | **1.16.0** | `1.0.0-rc.1` | 2026-09-29T13:02:27.857Z | "ElevenLabs React Library". 84 versions. Not deprecated. **This is the one for LetterLens.** |
| `@elevenlabs/client` | **1.26.0** | `1.0.0-rc.1` | 2026-09-29T13:04:10.786Z | "ElevenLabs JavaScript Client Library". 83 versions. Vanilla-JS / framework base. Not deprecated. |
| `@elevenlabs/elevenlabs-js` | **2.70.0** | `alpha` = `3.0.0-alpha.1` | 2026-09-28T15:33:07.933Z | **Server-side** Node SDK (REST API). Not a browser voice SDK. Use if you prefer an SDK over raw `fetch` for minting tokens. |
| `@elevenlabs/react-native` | not checked | — | — | S14: "For React Native, use `@elevenlabs/react-native`". |

Note the `next` dist-tag on both browser packages is `1.0.0-rc.1`, which is a *lower* semver than
`latest` 1.16.0 / 1.26.0. Do **not** install `@next` — it is an older release-candidate line, not a
preview of something newer. Pin exact versions.

### Deprecated (do NOT use)

| Package | `latest` | Deprecation message (verbatim) |
|---|---|---|
| `@11labs/react` | 0.2.0 (2025-08-13) | `This package is no longer maintained. Please use @elevenlabs/react for the latest version` |
| `@11labs/client` | 0.2.0 (2025-08-13) | `This package is no longer maintained. Please use @elevenlabs/client for the latest version` |
| `elevenlabs` | 1.59.0 (2025-05-15) | `This package has moved to @elevenlabs/elevenlabs-js` |

So the disambiguation the task asked for:

- `@elevenlabs/react` — **CURRENT**, the browser/React voice SDK.
- `@elevenlabs/client` — **CURRENT**, the vanilla-JS browser voice SDK (re-exported by the React one).
- `@11labs/react` — **DEPRECATED**, last published 2025-08-13.
- `elevenlabs` — **DEPRECATED**, and in any case it is the *server* SDK, not a browser voice SDK.

### Install

Verbatim from S2 / S14:

```shell
npm install @elevenlabs/react
```

Verbatim from S3:

```shell
npm install @elevenlabs/client
# or
yarn add @elevenlabs/client
# or
pnpm install @elevenlabs/client
```

S3 also carries this migration tip verbatim:

> Upgrading from an earlier version? Run `npx skills add elevenlabs/packages` to install the
> `elevenlabs:sdk-migration` skill for your AI coding agent, which automates import changes and API
> updates.

---

## 2. The exact React API

Source: S13 — `@elevenlabs/react@1.16.0/dist/index.d.ts`, verbatim:

```ts
export * from "@elevenlabs/client";
export { useScribe, AudioFormat, CommitStrategy, RealtimeEvents, } from "./scribe.js";
export type { ScribeStatus, TranscriptSegment, WordTimestamp, WordTimestampCharacter, ScribeCallbacks, ScribeHookOptions, UseScribeReturn, RealtimeConnection, } from "./scribe.js";
export { ConversationProvider } from "./conversation/ConversationProvider.js";
export { useConversationControls } from "./conversation/ConversationControls.js";
export { useConversationStatus } from "./conversation/ConversationStatus.js";
export { useConversationInput } from "./conversation/ConversationInput.js";
export { useConversationMode } from "./conversation/ConversationMode.js";
export { useConversationFeedback } from "./conversation/ConversationFeedback.js";
export { useRawConversation } from "./conversation/ConversationContext.js";
export { useConversation } from "./conversation/useConversation.js";
export { useConversationClientTool } from "./conversation/ConversationClientTools.js";
export type { UseConversationOptions } from "./conversation/useConversation.js";
export type { ConversationControlsValue } from "./conversation/ConversationControls.js";
export type { ConversationInputValue } from "./conversation/ConversationInput.js";
export type { ConversationStatus, ConversationStatusValue, } from "./conversation/ConversationStatus.js";
export type { ConversationModeValue } from "./conversation/ConversationMode.js";
export type { ConversationFeedbackValue } from "./conversation/ConversationFeedback.js";
export type { ConversationProviderProps } from "./conversation/ConversationProvider.js";
export type { HookOptions, HookCallbacks, ClientTool, ClientTools, ClientToolResult, } from "./conversation/types.js";
```

### 2.1 `ConversationProvider` is required

`ConversationProvider.d.ts`, verbatim:

```ts
import { type HookOptions } from "./types.js";
import { type ConversationInputProviderProps } from "./ConversationInput.js";
type ConversationInputControlProps = Pick<ConversationInputProviderProps, "isMuted" | "onMutedChange">;
export type ConversationProviderProps = React.PropsWithChildren<HookOptions & ConversationInputControlProps>;
export declare function ConversationProvider({ children, isMuted, onMutedChange, ...defaultOptions }: ConversationProviderProps): import("react").JSX.Element;
export {};
```

So **the provider accepts the entire `HookOptions` set** (session config + callbacks + client tools)
as *defaults*, plus the two controlled-mute props `isMuted` / `onMutedChange`.

Every hook except `useRawConversation` throws outside a provider. Verbatim error string from
`ConversationContext.js`:

```
"useRawConversationRef must be used within a ConversationProvider"
```

and `useRawConversation`'s own docstring, verbatim:

> Can be used outside a `ConversationProvider` — returns `null` in that case.

### 2.2 `useConversation()` — the convenience hook

`useConversation.d.ts`, verbatim:

```ts
import type { HookOptions } from "./types.js";
export type UseConversationOptions = HookOptions & {
    micMuted?: boolean;
    volume?: number;
};
/**
 * Convenience hook that combines all granular conversation hooks into a single
 * return value. Less performant than using individual hooks because any state
 * change in any sub-context triggers a re-render of the consuming component.
 *
 * Accepts optional `micMuted`, `volume`, session config, and callback props.
 * Session config and callbacks passed here are used as defaults when calling
 * `startSession()` without arguments. Callbacks are also registered with the
 * provider so they stay up-to-date across re-renders.
 *
 * Must be used within a `ConversationProvider`.
 */
export declare function useConversation(props?: UseConversationOptions): {
    startSession: (options?: HookOptions) => void;
    status: import("./ConversationStatus.js").ConversationStatus;
    message: string | undefined;
    isMuted: boolean;
    setMuted: (isMuted: boolean) => void;
    mode: "speaking" | "listening";
    isSpeaking: boolean;
    isListening: boolean;
    canSendFeedback: boolean;
    sendFeedback: (like: boolean | null, eventId?: number) => void;
    endSession: () => void;
    sendUserMessage: (text: string) => void;
    sendMultimodalMessage: (options: import("@elevenlabs/client").MultimodalMessageInput) => void;
    uploadFile: (file: Blob) => Promise<import("@elevenlabs/client").UploadFileResult>;
    sendContextualUpdate: (text: string, options?: import("@elevenlabs/client").ContextualUpdateOptions) => void;
    sendUserActivity: () => void;
    sendMCPToolApprovalResult: (toolCallId: string, isApproved: boolean) => void;
    setVolume: (options: {
        volume: number;
    }) => void;
    changeInputDevice: (config: Partial<import("@elevenlabs/client").FormatConfig> & import("@elevenlabs/client").InputDeviceConfig) => Promise<void>;
    changeOutputDevice: (config: Partial<import("@elevenlabs/client").FormatConfig> & import("@elevenlabs/client").OutputConfig) => Promise<void>;
    getInputByteFrequencyData: () => Uint8Array;
    getOutputByteFrequencyData: () => Uint8Array;
    getInputVolume: () => number;
    getOutputVolume: () => number;
    getId: () => string;
};
```

**Answers to the task's specific naming questions:**

| Task asked about | Reality in v1.16.0 |
|---|---|
| `useConversation`? | **Yes**, exists — but it is the *convenience* hook and requires a `ConversationProvider` ancestor. |
| `startSession` | Yes. Signature `(options?: HookOptions) => void`. **Returns `void`, not a Promise.** |
| `endSession` | Yes. `() => void`. |
| `status` | Yes. Type `"disconnected" \| "connecting" \| "connected" \| "error"` (React-level). |
| `isSpeaking` | Yes. Also `isListening` and `mode`. |
| `micMuted` | **No — renamed.** It is an *input option* (`micMuted?: boolean` on `UseConversationOptions`), while the *returned* state is **`isMuted`** with setter **`setMuted(isMuted: boolean)`**. Do not expect a returned `micMuted`. |
| `sendUserMessage` | Yes. `(text: string) => void`. |

### 2.3 Granular hooks (preferred for render performance)

| Hook | Returns |
|---|---|
| `useConversationControls()` | `ConversationControlsValue` — all action methods. Verbatim docstring: "All function references are stable and will never cause re-renders." |
| `useConversationStatus()` | `{ status: ConversationStatus; message?: string }` |
| `useConversationMode()` | `{ mode: "speaking" \| "listening"; isSpeaking: boolean; isListening: boolean }` |
| `useConversationInput()` | `{ isMuted: boolean; setMuted: (isMuted: boolean) => void }` |
| `useConversationFeedback()` | `ConversationFeedbackValue` — `canSendFeedback`, `sendFeedback` |
| `useRawConversation()` | the raw `@elevenlabs/client` `Conversation` instance, or `null` |
| `useConversationClientTool(name, handler)` | `void` — registers a tool for the component's lifetime |

`ConversationStatus.d.ts`, verbatim:

```ts
export type ConversationStatus = "disconnected" | "connecting" | "connected" | "error";
export type ConversationStatusValue = {
    status: ConversationStatus;
    message?: string;
};
```

> **Gotcha:** the React-level `ConversationStatus` includes **`"error"`** and omits
> `"disconnecting"`. The underlying client-level `Status` is different — see §6.3.

`ConversationMode.d.ts`, verbatim:

```ts
export type ConversationModeValue = {
    mode: "speaking" | "listening";
    isSpeaking: boolean;
    isListening: boolean;
};
```

`ConversationInput.d.ts`, verbatim:

```ts
export type ConversationInputValue = {
    isMuted: boolean;
    setMuted: (isMuted: boolean) => void;
};
export type ConversationInputProviderProps = React.PropsWithChildren<{
    /** Controlled mute state. If omitted, provider manages state internally. */
    isMuted?: boolean;
    /** Called whenever mute state is changed via setMuted. */
    onMutedChange?: (isMuted: boolean) => void;
}>;
```

`ConversationControls.d.ts`, verbatim:

```ts
export type ConversationControlsValue = {
    startSession: (options?: HookOptions) => void;
    endSession: () => void;
    sendUserMessage: (text: string) => void;
    sendMultimodalMessage: (options: MultimodalMessageInput) => void;
    uploadFile: (file: Blob) => Promise<UploadFileResult>;
    sendContextualUpdate: (text: string, options?: ContextualUpdateOptions) => void;
    sendUserActivity: () => void;
    sendMCPToolApprovalResult: (toolCallId: string, isApproved: boolean) => void;
    setVolume: (options: {
        volume: number;
    }) => void;
    changeInputDevice: (config: Partial<FormatConfig> & InputDeviceConfig) => Promise<void>;
    changeOutputDevice: (config: Partial<FormatConfig> & OutputConfig) => Promise<void>;
    /** Returns byte frequency data (0-255) for the input, focused on 100-8000 Hz. */
    getInputByteFrequencyData: () => Uint8Array;
    /** Returns byte frequency data (0-255) for the output, focused on 100-8000 Hz. */
    getOutputByteFrequencyData: () => Uint8Array;
    getInputVolume: () => number;
    getOutputVolume: () => number;
    getId: () => string;
};
```

### 2.4 The full options object — `HookOptions`

`react@1.16.0/dist/conversation/types.d.ts`, verbatim:

```ts
import type { SessionConfig, ClientToolsConfig, InputConfig, AudioWorkletConfig, OutputConfig, FormatConfig, Callbacks, ConversationLifecycleOptions, Location } from "@elevenlabs/client";
export type ClientToolResult = string | number | void;
export type ClientTool<Parameters extends Record<string, unknown> = Record<string, unknown>, Result extends ClientToolResult = ClientToolResult> = (parameters: Parameters) => Promise<Result> | Result;
export type ClientTools = Record<string, ClientTool>;
export type HookCallbacks = Pick<Callbacks, "onConnect" | "onDisconnect" | "onError" | "onMessage" | "onAudio" | "onModeChange" | "onStatusChange" | "onCanSendFeedbackChange" | "onDebug" | "onUnhandledClientToolCall" | "onVadScore" | "onInterruption" | "onAgentToolResponse" | "onAgentToolRequest" | "onConversationMetadata" | "onMCPToolCall" | "onMCPConnectionStatus" | "onAsrInitiationMetadata" | "onAgentChatResponsePart" | "onAgentReasoningResponsePart" | "onAgentResponseCorrection" | "onRichContent" | "onAudioAlignment" | "onGuardrailTriggered" | "onAgentTyping" | "onExternalAgentConnected" | "onExternalAgentDisconnected" | "onPing" | "onContextUsage" | "onIncomingEvent" | "onOutgoingEvent">;
export type HookOptions = Partial<SessionConfig & HookCallbacks & ConversationLifecycleOptions & ClientToolsConfig & InputConfig & OutputConfig & AudioWorkletConfig & FormatConfig & {
    serverLocation?: Location | string;
}>;
```

Note `HookOptions` is `Partial<SessionConfig & ...>`, which means at the type level the discriminated
union of `SessionConfig` (see §3) is flattened — TypeScript will **not** stop you from passing both
`agentId` and `conversationToken` to a React `startSession`. The runtime will. Pass exactly one.

---

## 3. Starting a session: agentId vs signed URL vs conversation token

Source: S13 — `@elevenlabs/client@1.26.0/dist/utils/BaseConnection.d.ts`, verbatim:

```ts
export type ConnectionType = "websocket" | "webrtc";

export type PublicSessionConfig = BaseSessionConfig & {
    agentId: string;
    connectionType?: ConnectionType;
    signedUrl?: never;
    conversationToken?: never;
    orchestrator?: never;
};
export type PrivateWebSocketSessionConfig = BaseSessionConfig & {
    signedUrl: string;
    connectionType?: "websocket";
    agentId?: never;
    conversationToken?: never;
    orchestrator?: never;
};
export type PrivateWebRTCSessionConfig = BaseSessionConfig & {
    conversationToken: string;
    connectionType?: "webrtc";
    agentId?: never;
    signedUrl?: never;
    orchestrator?: never;
};
export type SessionConfig = PublicSessionConfig | PrivateWebSocketSessionConfig | PrivateWebRTCSessionConfig | OrchestratorSessionConfig;
```

And `BaseSessionConfig`, verbatim (the shared part every variant gets):

```ts
export type BaseSessionConfig = {
    origin?: string;
    authorization?: string;
    livekitUrl?: string;
    webRtc?: {
        /**
         * ICE transport policy for the WebRTC connection. Set to "relay" to only
         * use TURN relay candidates, e.g. on networks that drop direct UDP flows.
         * Defaults to "all".
         */
        iceTransportPolicy?: "all" | "relay";
        /**
         * Whether to negotiate over a single peer connection (LiveKit's v1 join
         * protocol, which bundles the publisher offer in the JoinRequest). Set to
         * false to force the dual peer connection path, e.g. on platforms that
         * reject the microphone request at the point v1 issues it. Defaults to
         * livekit-client's own default, currently true.
         */
        singlePeerConnection?: boolean;
    };
    overrides?: {
        agent?: {
            prompt?: ConversationConfigOverrideAgentPrompt;
            firstMessage?: string;
            language?: Language;
        };
        tts?: {
            voiceId?: string;
            speed?: number;
            stability?: number;
            similarityBoost?: number;
        };
        asr?: {
            /** Keywords to boost ASR prediction probability for this conversation. */
            keywords?: string[];
        };
        conversation?: {
            textOnly?: boolean;
        };
    };
    customLlmExtraBody?: unknown;
    dynamicVariables?: Record<string, string | number | boolean>;
    toolMockConfig?: {
        /** Which tools to mock. Defaults to 'none'. */
        mockingStrategy?: "none" | "all" | "selected";
        /** Tool names to mock when mockingStrategy is 'selected'. */
        mockedToolNames?: string[];
        /** Behavior when mocked tool has no mock response. Defaults to 'raise_error'. */
        fallbackStrategy?: "raise_error" | "call_real_tool";
    };
    useWakeLock?: boolean;
    connectionDelay?: DelayConfig;
    textOnly?: boolean;
    userId?: string;
    environment?: string;
};
```

### 3.1 WebRTC vs WebSocket — which is current?

**Do not set `connectionType` manually.** Verbatim from S3 (and repeated in S2):

> The connection type is automatically inferred based on the conversation mode. Voice conversations
> use WebRTC and text-only conversations use WebSocket by default. You can still explicitly specify
> `connectionType: 'webrtc'` or `connectionType: 'websocket'` if needed.

So for LetterLens, which is a **voice** session: **WebRTC is current and the default.** WebRTC is
implemented over **LiveKit** — see the `livekitUrl` / `webRtc.singlePeerConnection` options above,
which name "LiveKit's v1 join protocol" explicitly. The three credential types map to transports:

| Credential option | Transport | Agent visibility |
|---|---|---|
| `agentId` | auto (WebRTC for voice) | public agent only |
| `conversationToken` | **WebRTC** | private agent |
| `signedUrl` | **WebSocket** | private agent |

WebRTC also pins the audio format. Verbatim from S3:

> In WebRTC mode the input format and sample rate are hardcoded to `pcm` and `48000` respectively.
> Changing those values when changing the input device is a no-op.

and:

> These methods are only available for voice conversations. In WebRTC mode the audio is hardcoded to
> use `pcm_48000`, meaning any visualization using the returned data might show different patterns
> to WebSocket connections.

### 3.2 Verbatim code example — modern React (from the package's own README, S14)

```tsx
import {
  ConversationProvider,
  useConversationControls,
  useConversationStatus,
} from "@elevenlabs/react";

function App() {
  return (
    {/* replace with your agent's ID */}
    <ConversationProvider agentId="agent_7101k5zvyjhmfg983brhmhkd98n6">
      <Conversation />
    </ConversationProvider>
  );
}

function Conversation() {
  const { startSession, endSession } = useConversationControls();
  const { status } = useConversationStatus();

  return (
    <div>
      <p>Status: {status}</p>
      <button
        onClick={() =>
          startSession({
            onConnect: ({ conversationId }) =>
              console.log("Connected:", conversationId),
            onError: (message) => console.error("Error:", message),
          })
        }
      >
        Start
      </button>
      <button onClick={() => endSession()}>End</button>
    </div>
  );
}
```

Note the shape: `agentId` on the **provider**, callbacks on the **`startSession` call**. Either may
carry either — provider props are defaults, `startSession(options)` overrides/merges onto them.

### 3.3 Verbatim code example — docs-page variant (S2)

```tsx
import {
  ConversationProvider,
  useConversationControls,
  useConversationStatus,
} from "@elevenlabs/react";

function App() {
  return (
    <ConversationProvider>
      <Agent />
    </ConversationProvider>
  );
}

function Agent() {
  const { startSession, endSession } = useConversationControls();
  const { status } = useConversationStatus();

  if (status === "connected") {
    return <button onClick={endSession}>End</button>;
  }

  return (
    <button onClick={() => startSession({ agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6" })}>
      Start
    </button>
  );
}
```

### 3.4 ⚠️ CONTRADICTION: `startSession` does NOT return a conversation id

S2 (the docs page) shows this example verbatim:

```js
const conversation = useConversation();
const conversationId = await conversation.startSession({
  agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6",
  userId: "user_9302xkm82nds93",
});
```

**That is stale for `@elevenlabs/react@1.16.0`.** The shipped type says
`startSession: (options?: HookOptions) => void`, and the compiled implementation in
`ConversationProvider.js` confirms it — the function body ends with a `lockRef.current.then(...)`
and has **no `return`**. Verbatim from that implementation:

```js
        lockRef.current = Conversation.startSession(startSessionOptions);
        lockRef.current.then(conv => {
            if (isStaleStartSession()) {
                return;
            }
            if (shouldEndRef.current) {
                conv
                    .endSession()
                    .catch(error => console.warn("Error ending session:", error));
                lockRef.current = null;
                return;
            }
            if (conversationRef.current !== conv) {
                thisSessionConv = conv;
                conversationRef.current = conv;
                setConversation(conv);
            }
            lockRef.current = null;
        }, (error) => {
            if (isStaleStartSession()) {
                return;
            }
            conversationRef.current = null;
            setConversation(null);
            lockRef.current = null;
            if (shouldEndRef.current) {
                return;
            }
            // The client SDK calls onStatusChange("disconnected") before
            // rejecting, but never calls onError — surface the failure here
            // so listeners (e.g. ConversationStatusProvider) transition to
            // the "error" state with a meaningful message.
            const message = error instanceof Error ? error.message : "Session failed to start";
            sessionOptions.onError?.(message, error);
        });
```

Consequences for LetterLens:

1. `await startSession(...)` resolves to `undefined` immediately — it does **not** wait for connect.
2. A failed start (denied mic, bad token) does **not** reject. It surfaces through **`onError`** and
   through `useConversationStatus()` transitioning to `status === "error"` with `message` set.
   Put all failure handling in `onError` / status, never in a `try/catch` around `startSession`.
3. Get the conversation id from `onConnect({ conversationId })` or `getId()`.
4. `startSession` is idempotence-guarded. Verbatim from the implementation:
   `if (conversationRef.current) { return; }` and `if (lockRef.current) { return; }` — so
   double-clicking "Start" is safe and silently no-ops.
5. The provider ends the session on unmount automatically (a `useEffect` cleanup calls `endSession`).

### 3.5 Vanilla-JS equivalents (S3), verbatim

Public agent:

```js
const conversation = await Conversation.startSession({
  agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6",
});
```

Private agent, WebSocket:

```js
// Client

const response = await fetch("/signed-url", yourAuthHeaders);
const signedUrl = await response.text();

const conversation = await Conversation.startSession({
  signedUrl,
});
```

Private agent, WebRTC:

```js
// Client

const response = await fetch("/conversation-token", yourAuthHeaders);
const conversationToken = await response.text();

const conversation = await Conversation.startSession({
  conversationToken,
});
```

In the **vanilla** SDK, `Conversation.startSession` *does* return a promise for a conversation
instance. Verbatim from S3:

> `startSession` returns a conversation instance (`VoiceConversation` or `TextConversation` depending
> on the mode) that can be used to control the session. The method will throw an error if the session
> cannot be established. This can happen if the user denies microphone access, or if the connection
> fails.

Typed, from `client@1.26.0/dist/index.d.ts`, verbatim:

```ts
interface ConversationNamespace {
    startSession<T extends PartialOptions>(options: T): T extends {
        textOnly: true;
    } ? Promise<TextConversation> : T extends {
        textOnly: false;
    } ? Promise<VoiceConversation> : Promise<TextConversation | VoiceConversation>;
}
export declare const Conversation: ConversationNamespace;
```

---

## 4. Client tools from the browser

### 4.1 Option key and handler signature

The option key is **`clientTools`**. From `client@1.26.0/dist/BaseConversation.d.ts`, verbatim:

```ts
export type ClientToolsConfig = {
    clientTools: Record<string, (parameters: any) => Promise<string | number | void> | string | number | void>;
};
```

The React SDK narrows it, from `react@1.16.0/dist/conversation/types.d.ts`, verbatim:

```ts
export type ClientToolResult = string | number | void;
export type ClientTool<Parameters extends Record<string, unknown> = Record<string, unknown>, Result extends ClientToolResult = ClientToolResult> = (parameters: Parameters) => Promise<Result> | Result;
export type ClientTools = Record<string, ClientTool>;
```

**Yes, the handler receives the parameters object** as its single argument — the agent's tool
arguments, destructurable. Verbatim example from S4:

```javascript
const conversation = await Conversation.startSession({
  clientTools: {
    logMessage: async ({message}) => {
      console.log(message);
    }
  },
});
```

Verbatim example from S4 of a tool that returns data:

```javascript
const clientTools = {
  getCustomerDetails: async () => {
    const customerData = {
      id: 123,
      name: "Alice",
      subscription: "Pro"
    };
    return customerData;
  }
};
```

### 4.2 Does returning a value send a result back to the agent? YES — and here is exactly how

This is the most load-bearing detail for LetterLens's tool round-trips, so it is recorded from the
compiled implementation rather than the prose. Verbatim from
`client@1.26.0/dist/BaseConversation.js` (`handleClientToolCall`):

```js
    async handleClientToolCall(event) {
        if (Object.prototype.hasOwnProperty.call(this.options.clientTools, event.client_tool_call.tool_name)) {
            try {
                const result = (await this.options.clientTools[event.client_tool_call.tool_name](event.client_tool_call.parameters)) ?? "Client tool execution successful."; // default client-tool call response
                // The API expects result to be a string, so we need to convert it if it's not already a string
                const formattedResult = typeof result === "object" ? JSON.stringify(result) : String(result);
                this.connection.sendMessage({
                    type: "client_tool_result",
                    tool_call_id: event.client_tool_call.tool_call_id,
                    result: formattedResult,
                    is_error: false,
                });
            }
            catch (e) {
                this.onError(`Client tool execution failed with following error: ${e?.message}`, {
                    clientToolName: event.client_tool_call.tool_name,
                });
                this.connection.sendMessage({
                    type: "client_tool_result",
                    tool_call_id: event.client_tool_call.tool_call_id,
                    result: `Client tool execution failed: ${e?.message}`,
                    is_error: true,
                });
            }
        }
        else {
            if (this.options.onUnhandledClientToolCall) {
                this.options.onUnhandledClientToolCall(event.client_tool_call);
                return;
            }
            this.onError(`Client tool with name ${event.client_tool_call.tool_name} is not defined on client`, {
                clientToolName: event.client_tool_call.tool_name,
            });
            this.connection.sendMessage({
                type: "client_tool_result",
                tool_call_id: event.client_tool_call.tool_call_id,
                result: `Client tool with name ${event.client_tool_call.tool_name} is not defined on client`,
                is_error: true,
            });
        }
    }
```

Precise behaviour, all branches:

1. **Return a string or number** → sent as `result: String(result)` with `is_error: false`.
2. **Return an object** → sent as `result: JSON.stringify(result)` with `is_error: false`. So
   returning an object **does** work at runtime (as S4's `getCustomerDetails` example shows) even
   though the TS type says `string | number | void`. Expect a TS complaint; it is a type/runtime gap.
   Safest for LetterLens: `return JSON.stringify(obj)` yourself and keep the type happy.
3. **Return `undefined` / `void`** → the SDK substitutes the literal string
   `"Client tool execution successful."` and still sends a result.
4. **Throw** → sends `result: "Client tool execution failed: <message>"` with **`is_error: true`**,
   and also fires `onError` with context `{ clientToolName }`. The agent is told, so it can recover.
5. **Tool not registered** → `onUnhandledClientToolCall(params)` if provided (and nothing is sent to
   the server); otherwise `onError` plus an `is_error: true` result.

The incoming event shape, verbatim from S7:

```json
{
  "type": "client_tool_call",
  "client_tool_call": {
    "tool_name": "search_database",
    "tool_call_id": "call_123456",
    "parameters": {
      "query": "user information",
      "filters": {
        "date": "2024-01-01"
      }
    }
  }
}
```

So the handler's argument is exactly `client_tool_call.parameters`.

### 4.3 Agent-side configuration is still required

Verbatim notes from S4:

> To enable the agent receiving data back, enable the **"Wait for response"** option in tool
> configuration.

and the API-level field: `"expects_response": false` when the tool doesn't require agent
acknowledgment; `true` when data should be returned to conversation context.

**For LetterLens: if you want the agent to use your tool's return value, you must set
`expects_response: true` / "Wait for response" on the agent's tool definition in the dashboard.**
Otherwise the SDK still sends `client_tool_result` but the agent will not wait for or consume it.

### 4.4 React: dynamic per-component registration

`react@1.16.0/dist/conversation/ConversationClientTools.d.ts`, verbatim:

```ts
/**
 * Registers a named client tool with the nearest `ConversationProvider`.
 * The tool is available during any active conversation and is automatically
 * unregistered when the component unmounts.
 *
 * The handler always reflects the latest closure value (ref pattern),
 * so it is safe to reference component state or props without listing
 * them as dependencies.
 *
 * @typeParam TTools - An interface mapping tool names to function signatures.
 * @typeParam TName  - The specific tool name (inferred from the first argument).
 * @param name    - The tool name (must match the name configured on the agent).
 * @param handler - The function invoked when the agent calls this tool.
 *
 * @example
 * ```tsx
 * type Tools = {
 *   get_weather: (params: { city: string }) => string;
 *   set_volume: (params: { level: number }) => void;
 * };
 *
 * useConversationClientTool<Tools>("get_weather", (params) => {
 *   return `Weather in ${params.city} is sunny.`;
 * });
 * ```
 */
export declare function useConversationClientTool<TTools extends ClientTools = Record<string, ClientTool>, TName extends string & keyof TTools = string & keyof TTools>(name: TName, handler: TTools[TName]): void;
```

Two guarantees in that docstring that matter for LetterLens:

- **"The handler always reflects the latest closure value (ref pattern), so it is safe to reference
  component state or props without listing them as dependencies."** — no stale-closure bug when a
  tool reads React state. This is the right way to let the agent read/write LetterLens UI state.
- **"automatically unregistered when the component unmounts."**

Also verbatim, on name collisions (`buildClientTools`):

> Creates a fresh clientTools object by merging option-provided tools with hook-registered tools from
> the registry. **Throws if a hook-registered tool name conflicts with an option-provided tool.**

So do not register the same tool name both in `clientTools` on the provider and via the hook.

Verbatim React example from S2:

```tsx
import { useConversationClientTool } from "@elevenlabs/react";
import { useState } from "react";

function MapComponent() {
  const [location, setLocation] = useState({ lat: 0, lng: 0 });

  useConversationClientTool("getLocation", () => {
    return `${location.lat},${location.lng}`;
  });

  useConversationClientTool("setLocation", (params: { lat: number; lng: number }) => {
    setLocation(params);
    return "Location updated";
  });

  return <Map center={location} />;
}
```

---

## 5. Dynamic variables at session start

Option key: **`dynamicVariables`** (camelCase in JS/TS; `dynamic_variables` in Python).

Authoritative type, from `client@1.26.0/dist/utils/BaseConnection.d.ts` → `BaseSessionConfig`,
verbatim:

```ts
    dynamicVariables?: Record<string, string | number | boolean>;
```

So the **allowed value types are exactly `string | number | boolean`**. Not objects, not arrays, not
`null`. Confirmed independently by S5, which lists String, Number and Boolean as the supported types.

Verbatim JS example from S5:

```javascript
this.conversation = await Conversation.startSession({
    agentId: 'agent_id_goes_here',
    dynamicVariables: {
        user_name: 'Angelo'
    },
});
```

Because `dynamicVariables` lives on `BaseSessionConfig`, and `HookOptions = Partial<SessionConfig & …>`,
it is accepted at **all three** levels in React: on `<ConversationProvider>`, on
`useConversation({…})`, and on `startSession({…})`. For LetterLens pass them on `startSession`,
since the per-letter values are only known at click time.

Python equivalent, verbatim from S5:

```python
dynamic_vars = {
    "user_name": "Angelo",
}

config = ConversationInitiationData(
    dynamic_variables=dynamic_vars
)
```

**Reserved system variables** (S5) — do not use the `system__` prefix for your own keys. They
auto-populate: `system__conversation_id`, `system__caller_id` (voice calls only), `system__time_utc`,
`system__conversation_history`. Verbatim: "All system variables use the reserved `system__` prefix and
update automatically throughout conversations."

### 5.1 Related: `overrides` (different thing, often confused)

`dynamicVariables` fills `{{placeholders}}` in a prompt. `overrides` **replaces** whole config
fields. Verbatim React example from S2:

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

For LetterLens, prefer `dynamicVariables` for per-letter context (cheaper, and no agent-side override
allowlisting needed). `overrides` require the corresponding override to be enabled on the agent.

---

## 6. Callbacks and events

### 6.1 The authoritative `Callbacks` type

From `client@1.26.0/dist/types.d.ts`, verbatim:

```ts
/**
 * Shared Callbacks, ensures all callbacks are implemented across all SDKs
 */
export type Callbacks = {
    onConnect?: (props: {
        conversationId: string;
    }) => void;
    onDisconnect?: (details: DisconnectionDetails) => void;
    onError?: (message: string, context?: any) => void;
    onMessage?: (props: MessagePayload) => void;
    onAudio?: (base64Audio: string) => void;
    onModeChange?: (prop: {
        mode: Mode;
    }) => void;
    onStatusChange?: (prop: {
        status: Status;
    }) => void;
    onCanSendFeedbackChange?: (prop: {
        canSendFeedback: boolean;
    }) => void;
    onUnhandledClientToolCall?: (params: ClientToolCallClientEvent["client_tool_call"]) => void;
    onVadScore?: (props: {
        vadScore: number;
    }) => void;
    onMCPToolCall?: (props: McpToolCallClientEvent["mcp_tool_call"]) => void;
    onMCPConnectionStatus?: (props: McpConnectionStatusClientEvent["mcp_connection_status"]) => void;
    onAgentToolRequest?: (props: AgentToolRequestClientEvent["agent_tool_request"]) => void;
    onAgentToolResponse?: (props: AgentToolResponseClientEvent["agent_tool_response"] | AgentToolResponseFullPayloadClientEvent["agent_tool_response_full_payload"]) => void;
    onConversationMetadata?: (props: ConversationMetadata["conversation_initiation_metadata_event"]) => void;
    onAsrInitiationMetadata?: (props: AsrInitiationMetadataEvent["asr_initiation_metadata_event"]) => void;
    onInterruption?: (props: Interruption["interruption_event"]) => void;
    onAgentResponseCorrection?: (props: AgentResponseCorrection["agent_response_correction_event"]) => void;
    onAgentChatResponsePart?: (props: AgentChatResponsePartClientEvent["text_response_part"]) => void;
    onAgentReasoningResponsePart?: (props: AgentReasoningResponsePartClientEvent["reasoning_response_part"]) => void;
    onRichContent?: (props: RichContentClientEvent["rich_content"]) => void;
    onGuardrailTriggered?: () => void;
    onAudioAlignment?: (props: AudioAlignmentEvent) => void;
    onAgentTyping?: (props: AgentTypingClientEvent["agent_typing_event"]) => void;
    onExternalAgentConnected?: () => void;
    onExternalAgentDisconnected?: () => void;
    onPing?: (props: Ping["ping_event"]) => void;
    onContextUsage?: (props: ContextUsageClientEvent["context_usage_event"]) => void;
    onDebug?: (props: any) => void;
    /**
     * Called for every incoming event received from the server.
     */
    onIncomingEvent?: (props: any) => void;
    /**
     * Called for every outgoing event sent to the server.
     */
    onOutgoingEvent?: (props: any) => void;
};
```

And the runtime key list, verbatim:

```ts
export declare const CALLBACK_KEYS: readonly ["onConnect", "onDisconnect", "onError", "onMessage", "onAudio", "onModeChange", "onStatusChange", "onCanSendFeedbackChange", "onUnhandledClientToolCall", "onVadScore", "onMCPToolCall", "onMCPConnectionStatus", "onAgentToolRequest", "onAgentToolResponse", "onConversationMetadata", "onAsrInitiationMetadata", "onInterruption", "onAgentResponseCorrection", "onAgentChatResponsePart", "onAgentReasoningResponsePart", "onRichContent", "onAudioAlignment", "onGuardrailTriggered", "onAgentTyping", "onExternalAgentConnected", "onExternalAgentDisconnected", "onPing", "onContextUsage", "onDebug", "onIncomingEvent", "onOutgoingEvent"];
```

### 6.2 Task's checklist, resolved

| Callback asked about | Exists? | Exact signature |
|---|---|---|
| `onConnect` | ✅ | `(props: { conversationId: string }) => void` |
| `onDisconnect` | ✅ | `(details: DisconnectionDetails) => void` — note it is **not** a DOM `CloseEvent` |
| `onMessage` | ✅ | `(props: MessagePayload) => void` — see §6.4 |
| `onError` | ✅ | `(message: string, context?: any) => void` — **message string first, not an Error object** |
| `onDebug` | ✅ | `(props: any) => void` |
| `onStatusChange` | ✅ | `(prop: { status: Status }) => void` |
| `onModeChange` | ✅ | `(prop: { mode: Mode }) => void` |

Also present and useful for LetterLens: `onInterruption`, `onVadScore` (live mic-activity meter),
`onAudioAlignment` (per-character timing for karaoke-style highlighting),
`onAgentChatResponsePart` (streaming agent text), `onPing` (latency readout),
`onIncomingEvent` / `onOutgoingEvent` (wire-level debugging).

Also documented in S3 but **not** in `Callbacks`: nothing — S3 additionally names
`onCanSendFeedbackChange` and `onAudioAlignment`, both of which are present above.

> **React note:** every callback in `HookCallbacks` can be given at provider level *and* hook level
> *and* `startSession` level, and the React SDK **composes** them rather than overwriting — see
> `ListenerMap` and `listenerMap.compose()` in `ConversationProvider.js`. So a child component can
> add its own `onMessage` without stomping the provider's. Verbatim comment from the type file:
> "Used by the React SDK to pre-initialize listener maps for callback composition."

### 6.3 `Status`, `Mode`, `Role`, `DisconnectionDetails` — verbatim

```ts
/**
 * Role in the conversation
 */
export type Role = "user" | "agent";
/**
 * Current mode of the conversation
 */
export type Mode = "speaking" | "listening";
/**
 * Connection status of the conversation
 */
export type Status = "disconnected" | "connecting" | "connected" | "disconnecting";
/**
 * Platform-agnostic representation of the event that triggered a disconnection.
 * Replaces the former `Event` / `CloseEvent` DOM constructors which are
 * not available on React Native.
 */
export type DisconnectionContext = {
    type: string;
    reason?: string;
    code?: number;
};
/**
 * Reason for the disconnection
 */
export type DisconnectionDetails = {
    reason: "error";
    message: string;
    context: DisconnectionContext;
    closeCode?: number;
    closeReason?: string;
} | {
    reason: "agent";
    context?: DisconnectionContext;
    closeCode?: number;
    closeReason?: string;
} | {
    reason: "user";
};
```

⚠️ **Two different status enums.** Client-level `Status` (what `onStatusChange` gives you) is
`"disconnected" | "connecting" | "connected" | "disconnecting"`. React-level `ConversationStatus`
(what `useConversationStatus()` gives you) is `"disconnected" | "connecting" | "connected" | "error"`.
`"error"` is synthesised by the React layer; `"disconnecting"` is swallowed by it. Pick one source
and stick to it. For UI, use `useConversationStatus()`.

`DisconnectionDetails.reason` is the clean way to distinguish "user hung up" (`"user"`) from
"agent ended the call" (`"agent"`) from "it broke" (`"error"`, which also carries `message`).

### 6.4 ⭐ `onMessage` payload — the live transcript shape

This is the one LetterLens needs for rendering a transcript. Verbatim from
`client@1.26.0/dist/types.d.ts`:

```ts
export interface MessagePayload {
    message: string;
    event_id: number;
    /** Stable identifier for an agent response across streamed parts and resends. */
    response_id?: string;
    /**
     * @deprecated use {@link role} instead.
     */
    source: "user" | "ai";
    role: Role;
    /**
     * Files attached to an agent message, e.g. relayed from a human agent
     * reply. Only present on agent messages.
     */
    attachments?: MessageAttachment[];
}
```

**Yes — it includes `source: 'user' | 'ai'` and `message` text, exactly as the task hypothesised.**
But `source` is **`@deprecated`**; the replacement is `role: "user" | "agent"`. Note the asymmetry:
`source` uses `"ai"`, `role` uses `"agent"`.

And here is the exact emission, from `client@1.26.0/dist/BaseConversation.js` — proof that both
fields are always populated and that agent and user turns both route through `onMessage`:

```js
    handleAgentResponse(event) {
        this.currentEventId = event.agent_response_event.event_id;
        if (this.options.onMessage) {
            this.options.onMessage({
                source: "ai",
                role: "agent",
                message: event.agent_response_event.agent_response,
                event_id: event.agent_response_event.event_id,
                ...(event.agent_response_event.response_id
                    ? { response_id: event.agent_response_event.response_id }
                    : {}),
                attachments: event.agent_response_event.attachments,
            });
```

```js
    handleUserTranscript(event) {
        if (this.options.onMessage) {
            this.options.onMessage({
                source: "user",
                role: "user",
                message: event.user_transcription_event.user_transcript,
                event_id: event.user_transcription_event.event_id,
            });
        }
    }
```

**Recommended LetterLens transcript handler:**

```tsx
import { useConversation } from "@elevenlabs/react";
import type { MessagePayload } from "@elevenlabs/react"; // re-exported from @elevenlabs/client

type Turn = { id: number; who: "user" | "agent"; text: string };

const [turns, setTurns] = useState<Turn[]>([]);

useConversation({
  onMessage: (m: MessagePayload) => {
    setTurns(prev => [...prev, { id: m.event_id, who: m.role, text: m.message }]);
  },
});
```

Important transcript caveats, all verified from the compiled source:

- `onMessage` fires only on **final** `user_transcript` events. **Tentative/partial agent responses
  do NOT go to `onMessage`** — they go to `onDebug`. Verbatim:

  ```js
      handleTentativeAgentResponse(event) {
          if (this.options.onDebug) {
              this.options.onDebug({
                  type: "tentative_agent_response",
                  response: event.tentative_agent_response_internal_event
                      .tentative_agent_response,
              });
          }
      }
  ```

  So S3's description of `onMessage` as handling "tentative or final transcriptions" is **misleading**
  for the agent side. If you want streaming agent text, use `onAgentChatResponsePart`.
- `agent_response_correction` does **not** come through `onMessage` either — it has its own
  `onAgentResponseCorrection` callback. Its payload, verbatim from S7:

  ```json
  {
    "type": "agent_response_correction",
    "agent_response_correction_event": {
      "original_agent_response": "Let me tell you about the complete history...",
      "corrected_agent_response": "Let me tell you about..."
    }
  }
  ```

  **For a correct transcript after a barge-in you must handle this** — the agent was cut off
  mid-sentence and the already-rendered `onMessage` text is now wrong. Reconcile using
  `response_id` / `event_id`.
- `event_id` is a usable React key, and `response_id` is described verbatim as a "Stable identifier
  for an agent response across streamed parts and resends" — use it to dedupe resends.

### 6.5 Wire-level client event payloads (S7), verbatim

```json
{
  "type": "user_transcript",
  "user_transcription_event": {
    "user_transcript": "Hello, how can you help me today?"
  }
}
```

```json
{
  "type": "agent_response",
  "agent_response_event": {
    "agent_response": "Hello, how can I assist you today?"
  }
}
```

```json
{
  "ping_event": {
    "event_id": 123456,
    "ping_ms": 50
  },
  "type": "ping"
}
```

```json
{
  "audio_event": {
    "audio_base_64": "base64_encoded_audio_string",
    "event_id": 12345,
    "alignment": {
      "chars": ["H", "e", "l", "l", "o"],
      "char_durations_ms": [50, 30, 40, 40, 60],
      "char_start_times_ms": [0, 50, 80, 120, 160]
    }
  },
  "type": "audio"
}
```

```json
{
  "type": "vad_score",
  "vad_score_event": {
    "vad_score": 0.95
  }
}
```

The SDK auto-replies to `ping` with `pong`; verbatim from the `onPing` docstring:

> Called for every `ping` event received from the server. The SDK automatically replies with a
> `pong`, so this callback is purely informational — a common use is surfacing connection latency to
> the user.

### 6.6 ⚠️ Events must be enabled on the agent

Verbatim warning from S3:

> Not all client events are enabled by default for an agent. If you have enabled a callback but
> aren't seeing events come through, ensure that your ElevenLabs agent has the corresponding event
> enabled. You can do this in the "Advanced" tab of the agent settings in the ElevenLabs dashboard.

S7 specifically names these as needing explicit enabling in the agent's `client_events` config:
`agent_response_metadata`, `agent_tool_response_full_payload`, `agent_chat_response_part` (in voice
conversations), `agent_reasoning_response_part`, `agent_response_complete`, `guardrail_triggered`.

**LetterLens action item:** before debugging a silent callback, check the agent's Advanced →
Client Events list. In particular `interruption` (§7) and `agent_chat_response_part` are the two most
likely to be off and to silently break a feature.

---

## 7. Interruption / barge-in

### 7.1 Is it automatic?

**Partly.** Two halves:

**Client half — automatic, nothing to configure or write.** The SDK handles the server's
`interruption` event by immediately flushing queued output audio and flipping mode to listening.
Verbatim from `client@1.26.0/dist/VoiceConversation.js`:

```js
    handleInterruption(event) {
        super.handleInterruption(event);
        this.updateMode("listening");
        this.output.interrupt();
    }
```

and verbatim from `BaseConversation.js`:

```js
    handleInterruption(event) {
        if (event.interruption_event) {
            this.lastInterruptTimestamp = event.interruption_event.event_id;
            if (this.options.onInterruption) {
                this.options.onInterruption({
                    event_id: event.interruption_event.event_id,
                });
            }
        }
    }
```

There is also a **stale-audio guard**: audio chunks whose `event_id` predates the last interruption
are dropped, so the agent cannot resume a cut-off sentence. Verbatim from `VoiceConversation.js`:

```js
    handleAudio(event) {
        super.handleAudio(event);
        if (event.audio_event.alignment && this.options.onAudioAlignment) {
            this.options.onAudioAlignment(event.audio_event.alignment);
        }
        if (this.lastInterruptTimestamp <= event.audio_event.event_id) {
            if (event.audio_event.audio_base_64) {
                this.options.onAudio?.(event.audio_event.audio_base_64);
                // Audio routing is handled by attachConnectionToOutput for WebSocket
                // WebRTC handles audio playback directly through LiveKit tracks
            }
```

So: no client code, no VAD wiring, no "stop playback" call. You write nothing. `onInterruption` exists
purely so the UI can react (e.g. clear a partially-rendered agent bubble). The `interruption_event`
payload the callback receives is `{ event_id: number }`.

**Server half — must be enabled on the agent.** Verbatim from S8:

> To enable interruptions, make sure interruption is a selected client event.

and:

> Interruption settings can be configured in the agent's **Advanced** tab under **Client Events**.

**This is the barge-in gotcha.** If `interruption` is not in the agent's `client_events`, the server
never sends the event, `handleInterruption` never runs, and the agent will talk over the user no
matter what the browser does. LetterLens must verify this checkbox on the agent config.

### 7.2 Related turn-taking config (S8)

| Setting | Path | Values |
|---|---|---|
| Turn timeout | `conversation_config.turn.turn_timeout` | seconds, range 1–30 |
| Turn eagerness | `conversation_config.turn.turn_eagerness` | `"patient"` \| `"normal"` \| `"eager"` (default appears to be `"normal"`) |
| Soft timeout / filler audio | `conversation_config.turn.soft_timeout_config` | handles LLM response delays with filler audio |

Verbatim guidance from S8 on `turn_timeout`:

> Choose an appropriate timeout duration based on your use case. Shorter timeouts create more
> responsive conversations but may interrupt users who need more time to respond, leading to a less
> natural conversation.

Client-side nudge against the agent interrupting a *typing* user — `sendUserActivity()`, verbatim
from S3:

> Notifies the agent about user activity. The agent will not attempt to speak for at least 2 seconds
> after the user activity is detected. This can be used to prevent the agent from interrupting the
> user when they are typing.

```js
textInput.addEventListener("input", () => {
  conversation.sendUserActivity();
});
```

There is also a separate page, identified but not fetched in depth:
`https://elevenlabs.io/docs/eleven-agents/customization/tools/tool-configuration/tool-interruptions.md`
— "Control whether users can interrupt the agent while a tool runs." Relevant if a LetterLens client
tool is slow.

---

## 8. Public vs private agents, and minting credentials

### 8.1 The gate

Source: S6. The relevant agent settings, exact field names:

- **`enable_auth`** — "Activates signed URL requirement."
- **`allowlist`** — "Array of approved hostnames."

So: **a public agent (`enable_auth` off) can be started from the browser with just `agentId`, no
backend needed.** A private agent (`enable_auth` on) requires a server-minted credential, because
minting needs the ElevenLabs API key, which must never reach the browser.

S6 on the allowlist: supports "exact matching on hostnames" and permits "up to 10 unique hostnames."
Subdomains require separate entries (e.g. both `example.com` and `app.example.com`).

**For a hackathon, the pragmatic call:** a public agent plus an allowlist of your deploy hostname is
the fastest path and needs zero backend. But the allowlist is the only thing stopping someone else
burning your credits, and allowlists match a client-reported hostname, so treat it as deterrence, not
security. If LetterLens has any backend at all, mint tokens — it is ~10 lines.

### 8.2 WebRTC: conversation token (recommended for voice)

Source: S9 (API reference) + S3/S2 (code).

- **Method and path:** `GET /v1/convai/conversation/token`
- **Full URL:** `https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=<agent_id>`
- **Required header:** `xi-api-key: <YOUR_ELEVENLABS_API_KEY>`
- **Query parameters** (from S9):

| Param | Type | Required | Notes (verbatim where quoted) |
|---|---|---|---|
| `agent_id` | string | **required** | "Agent id (agent_…) or speech engine external id (seng_)" |
| `participant_name` | string | optional | "Optional custom participant name" |
| `branch_id` | string | optional | |
| `version_id` | string | optional | |
| `environment` | string | optional | Defaults to `'production'` |
| `debug_events_request` | boolean | optional | default `false` |

- **200 response schema** (S9), verbatim:

```json
{
  "token": "string",
  "conversation_id": "string"
}
```

  ⚠️ Note: the response carries **both** `token` and `conversation_id`. The docs' example server code
  returns only `body.token`. If LetterLens wants the conversation id before connecting (e.g. to
  pre-create a DB row), return both from your endpoint rather than just the token.

- **Backend code**, verbatim from S3:

```js
// Node.js server

app.get("/conversation-token", yourAuthMiddleware, async (req, res) => {
  const response = await fetch(
    `https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=${process.env.AGENT_ID}`,
    {
      headers: {
        // Requesting a conversation token requires your ElevenLabs API key
        // Do NOT expose your API key to the client!
        "xi-api-key": process.env.ELEVENLABS_API_KEY,
      },
    }
  );

  if (!response.ok) {
    return res.status(500).send("Failed to get conversation token");
  }

  const body = await response.json();
  res.send(body.token);
});
```

- **Or via the server SDK**, verbatim from S9:

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

async function main() {
    const client = new ElevenLabsClient();
    await client.conversationalAi.conversations.getWebrtcToken({
        agentId: "agent_3701k3ttaq12ewp8b7qv5rfyszkz",
    });
}
main();
```

  (Note the SDK method is named `getWebrtcToken`, and the docs page slug is `get-webrtc-token.md`,
  even though the page title and the wire path both say "conversation token". All three refer to the
  same endpoint.)

- **Client side**, verbatim from S3:

```js
const response = await fetch("/conversation-token", yourAuthHeaders);
const conversationToken = await response.text();

const conversation = await Conversation.startSession({
  conversationToken,
});
```

  And verbatim from S3: "Once you have the token, providing it to `startSession` will initiate the
  conversation using WebRTC."

### 8.3 WebSocket: signed URL

- **Method and path:** `GET /v1/convai/conversation/get-signed-url?agent_id=<agent_id>`
- **Required header:** `xi-api-key: your-api-key`
- **Response shape** (S6), verbatim:

```json
{
  "signed_url": "wss://api.elevenlabs.io/v1/convai/conversation?agent_id=<id>&conversation_signature=<token>"
}
```

- **Expiry** (S6), verbatim:

> Signed URLs are valid for 15 minutes. The conversation session can last longer, but the
> conversation must be initiated within the 15 minute window.

- **Backend code**, verbatim from S3:

```js
// Node.js server

app.get("/signed-url", yourAuthMiddleware, async (req, res) => {
  const response = await fetch(
    `https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=${process.env.AGENT_ID}`,
    {
      method: "GET",
      headers: {
        // Requesting a signed url requires your ElevenLabs API key
        // Do NOT expose your API key to the client!
        "xi-api-key": process.env.XI_API_KEY,
      },
    }
  );

  if (!response.ok) {
    return res.status(500).send("Failed to get signed URL");
  }

  const body = await response.json();
  res.send(body.signed_url);
});
```

  (Mind the env var name drift between the docs' two examples: `XI_API_KEY` here,
  `ELEVENLABS_API_KEY` in the token example. Pick one for LetterLens.)

- **Client side**, verbatim from S3:

```js
const response = await fetch("/signed-url", yourAuthHeaders);
const signedUrl = await response.text();

const conversation = await Conversation.startSession({
  signedUrl,
});
```

S11 (Next.js quickstart) adds: signed URLs have expiration limits, active conversations persist
beyond expiration, and refresh logic is recommended for production.

### 8.4 Recommended LetterLens pattern (Next.js App Router)

Built from the verified shapes above. Note it returns `conversation_id` too, which the docs example
drops.

```ts
// app/api/elevenlabs/token/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  const res = await fetch(
    `https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=${process.env.ELEVENLABS_AGENT_ID}`,
    { headers: { "xi-api-key": process.env.ELEVENLABS_API_KEY! }, cache: "no-store" }
  );
  if (!res.ok) {
    return NextResponse.json({ error: "token_mint_failed" }, { status: 502 });
  }
  // { token: string, conversation_id: string }
  const body = await res.json();
  return NextResponse.json(
    { token: body.token, conversationId: body.conversation_id },
    { headers: { "Cache-Control": "no-store" } }
  );
}
```

```tsx
"use client";
import {
  ConversationProvider,
  useConversationControls,
  useConversationStatus,
  useConversationMode,
} from "@elevenlabs/react";
import { useState } from "react";

export function LetterLensVoice({ letterId, letterText }: { letterId: string; letterText: string }) {
  return (
    <ConversationProvider
      onError={(message, context) => console.error("[11labs]", message, context)}
    >
      <Session letterId={letterId} letterText={letterText} />
    </ConversationProvider>
  );
}

function Session({ letterId, letterText }: { letterId: string; letterText: string }) {
  const { startSession, endSession } = useConversationControls();
  const { status, message } = useConversationStatus();
  const { isSpeaking } = useConversationMode();
  const [turns, setTurns] = useState<{ id: number; who: "user" | "agent"; text: string }[]>([]);

  async function start() {
    // Ask for the mic BEFORE connecting, so the prompt appears in context
    // and a denial is distinguishable from a connection failure.
    await navigator.mediaDevices.getUserMedia({ audio: true });

    const { token } = await fetch("/api/elevenlabs/token").then(r => r.json());

    // NOTE: returns void. Do not await for an id; use onConnect.
    startSession({
      conversationToken: token,            // => WebRTC
      dynamicVariables: {                  // string | number | boolean only
        letter_id: letterId,
        letter_text: letterText,
      },
      onConnect: ({ conversationId }) => console.log("connected", conversationId),
      onMessage: m => setTurns(p => [...p, { id: m.event_id, who: m.role, text: m.message }]),
      onDisconnect: details => console.log("disconnected:", details.reason),
    });
  }

  return (
    <div>
      <p>{status}{message ? ` — ${message}` : ""}{isSpeaking ? " (agent speaking)" : ""}</p>
      {status === "connected"
        ? <button onClick={endSession}>End</button>
        : <button onClick={start} disabled={status === "connecting"}>Start</button>}
      <ul>{turns.map(t => <li key={t.id}><b>{t.who}:</b> {t.text}</li>)}</ul>
    </div>
  );
}
```

---

## 9. Microphone permissions, HTTPS / localhost

### 9.1 What the ElevenLabs docs actually say

Verbatim from S2:

> ElevenAgents requires microphone access for voice conversations.

Verbatim from S3:

> This will establish a connection and start using the microphone to communicate with the ElevenLabs
> Agents agent. Consider explaining and allowing microphone access in your app's UI before starting
> the conversation:

```js
// call after explaining to the user why the microphone access is needed
await navigator.mediaDevices.getUserMedia({ audio: true });
```

Verbatim from S11:

```js
await navigator.mediaDevices.getUserMedia({ audio: true })
```

**Pattern:** call `getUserMedia({ audio: true })` yourself, from a user gesture, *before*
`startSession`. This splits two failure modes that otherwise look identical: "user denied the mic" vs
"the session could not connect." Especially important in React, where `startSession` does not reject
(§3.4) — without the pre-flight you learn about a denied mic only as an `onError` string.

**Avoiding the prompt entirely:** text-only mode skips it. Verbatim from S2:

> If your agent is configured to run in text-only mode…you can use this flag to use a lighter
> version of the conversation. In that case, the user will not be asked for microphone permissions
> and no audio context will be created.

```ts
const conversation = useConversation({
  textOnly: true,
});
```

### 9.2 HTTPS / secure-context requirement — ⚠️ confidence: LOW from ElevenLabs docs

**I could not find any statement in the ElevenLabs documentation about HTTPS, secure contexts, or
localhost requirements.** I grepped the full docs index (S1, 1374 lines) for `microphone`,
`permission` and `https` and found no page covering browser security prerequisites, and neither S2,
S3 nor S11 mentions it.

What is true regardless, as a **browser platform constraint rather than an ElevenLabs one**:
`navigator.mediaDevices` is only exposed in a secure context, so the page must be served over HTTPS
or from a localhost-family origin (`http://localhost`, `http://127.0.0.1`). This is the WebRTC /
`getUserMedia` platform rule, **not** something verified against an ElevenLabs page in this task. If
this becomes load-bearing for a deploy decision, confirm against MDN's `MediaDevices` page or
`developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts` before relying on it.

Practical consequence for LetterLens either way: `http://localhost:3000` works in dev; a LAN IP like
`http://192.168.x.x:3000` will not give you a microphone. Test on localhost or an HTTPS tunnel.

### 9.3 Mic control during a session

| Thing | API |
|---|---|
| Mute/unmute (React) | `const { isMuted, setMuted } = useConversationInput()` |
| Mute at session start | `micMuted?: boolean` on `useConversation({…})`, or `isMuted` prop on `ConversationProvider` |
| Controlled mute | `ConversationProvider`'s `isMuted` + `onMutedChange` props |
| Mute (vanilla) | `conversation.setMicMuted(true)` / `(false)` |
| Pick a device | `inputDeviceId` at session start, or `changeInputDevice({ inputDeviceId })` mid-session |
| Live mic level | `getInputVolume()` (0–1; verbatim from S3: "where `0` is -100 dB and `1` is -30 dB"), `getInputByteFrequencyData()` (0–255, focused on 100–8000 Hz) |
| Live VAD | `onVadScore: ({ vadScore }) => …` |

Verbatim from S3 on mute:

```js
// Mute the microphone
conversation.setMicMuted(true);

// Unmute the microphone
conversation.setMicMuted(false);
```

Verbatim from S3 on device selection at start:

```js
const conversation = await Conversation.startSession({
  agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6",
  // Alternatively you can provide a device ID when starting the session
  // Useful if you want to start the conversation with a non-default device
  inputDeviceId: "a1b2c3d4e5f6",
});

// Change to a specific input device
await conversation.changeInputDevice({
  sampleRate: 16000,
  format: "pcm",
  preferHeadphonesForIosDevices: true,
  inputDeviceId: "a1b2c3d4e5f6",
});
```

Verbatim from S3: "If the device ID is invalid, the default device will be used instead." And:
"Device switching only works for voice conversations. If no specific `deviceId` is provided, the
browser will use its default device selection."

### 9.4 CSP note (may matter for a deployed Next.js app)

The WebSocket path uses AudioWorklets loaded from blob:/data: URLs. The SDK offers a self-hosting
escape hatch. Verbatim from `client@1.26.0/dist/BaseConversation.d.ts`:

```ts
/** Allows self-hosting the worklets to avoid whitelisting blob: and data: in the CSP script-src  */
export type AudioWorkletConfig = {
    workletPaths?: {
        rawAudioProcessor?: string;
        audioConcatProcessor?: string;
    };
    libsampleratePath?: string;
};
```

If LetterLens ships a strict CSP and the voice session fails with a worklet error, either allow
`blob:` in `script-src` or set `workletPaths`. Less likely to bite on the WebRTC path, where LiveKit
handles playback.

---

## 10. Other session options and methods worth knowing

All from `BaseSessionConfig` (§3) unless noted.

| Option | Type | Use for LetterLens |
|---|---|---|
| `userId` | `string` | Tag the conversation with your own user id for later analytics lookup. |
| `textOnly` | `boolean` | Skip mic + audio context entirely. |
| `useWakeLock` | `boolean` | Keep the screen awake during a long voice session (mobile). |
| `connectionDelay` | `{ default: number; android?: number; ios?: number }` | Platform-specific connect delay. |
| `customLlmExtraBody` | `unknown` | Extra body passed to a custom LLM. |
| `serverLocation` | `Location \| string` (React `HookOptions` only) | Region pinning. |
| `webRtc.iceTransportPolicy` | `"all" \| "relay"` | Verbatim: 'Set to "relay" to only use TURN relay candidates, e.g. on networks that drop direct UDP flows. Defaults to "all".' Try this if a demo venue's wifi blocks UDP. |
| `toolMockConfig` | see §3 | Mock tools while developing — `mockingStrategy: "none" \| "all" \| "selected"`. Useful for demoing without live integrations. |
| `environment` | `string` | Defaults to `'production'`. |
| `origin`, `authorization`, `livekitUrl` | `string` | Normally set by the SDK; the React provider computes `origin` and `livekitUrl` from `serverLocation`. |

Conversation methods (S3) available via `useConversationControls()`:
`getId()`, `setVolume({ volume })` (0–1), `getInputVolume()` / `getOutputVolume()`,
`sendFeedback(like, eventId?)`, `sendContextualUpdate(text, options?)`, `sendUserMessage(text)`,
`sendUserActivity()`, `uploadFile(blob)`, `sendMultimodalMessage({ text, fileIds })`,
`sendMCPToolApprovalResult(toolCallId, isApproved)`, `changeInputDevice`, `changeOutputDevice`,
`getInputByteFrequencyData()`, `getOutputByteFrequencyData()`.

Verbatim on `sendContextualUpdate` from S3 — useful for telling the agent the user scrolled to a new
part of the letter without prompting a reply:

```js
conversation.sendContextualUpdate(
  "User navigated to another page. Consider it for next response, but don't react to this contextual update."
);
```

Verbatim on `sendUserMessage` from S3: "Can be used to let the user type in the message instead of
using the microphone. Unlike `sendContextualUpdate`, this will be treated as a user message and will
prompt the agent to take its turn in the conversation."

Verbatim on `sendFeedback` from S3: "Feedback is always correlated to the most recent agent response
and can be sent only once per response. You can listen to `onCanSendFeedbackChange` to know if
feedback can be sent at the given moment."

```js
conversation.sendFeedback(true); // positive feedback
conversation.sendFeedback(false); // negative feedback
```

Verbatim on `setVolume` from S3: "A method to set the output volume of the conversation. Accepts
object with volume field between 0 and 1."

```js
await conversation.setVolume({ volume: 0.5 });
```

---

## 11. Blockers, contradictions and open questions

### Confirmed blockers / spec corrections

1. **`startSession` returns `void` in the React SDK.** Any design that awaits it for a conversation
   id, or wraps it in `try/catch` for error handling, is wrong. Use `onConnect` and `onError` /
   `useConversationStatus()`. Verified against both the `.d.ts` and the compiled implementation; the
   published docs page (S2) still shows the old `await`-returns-id form.
2. **`ConversationProvider` is mandatory.** Every conversation hook except `useRawConversation`
   throws outside it. A design that just calls `useConversation()` in a leaf component will crash.
3. **No returned `micMuted`.** The returned state is `isMuted` / `setMuted`; `micMuted` is only an
   input option. Rename in any spec that says otherwise.
4. **`source` on `MessagePayload` is `@deprecated`.** It works and is populated, but build on
   `role: "user" | "agent"`. Note `source` says `"ai"` where `role` says `"agent"`.
5. **Barge-in needs the `interruption` client event enabled on the agent** (S8). Client-side handling
   is already automatic; the dashboard checkbox is the failure point.
6. **Client tools that must return data to the agent need "Wait for response" /
   `expects_response: true`** on the agent's tool config (S4). The SDK always sends a result; the
   agent ignores it unless configured to wait.
7. **`dynamicVariables` values must be `string | number | boolean`.** Serialize any object or array
   yourself (e.g. the letter's structured fields as a JSON string).
8. **Do not install `@elevenlabs/react@next`** — `next` is `1.0.0-rc.1`, older than `latest` 1.16.0.
9. **Two incompatible status enums** (React `"error"` vs client `"disconnecting"`) — see §6.3.
10. **Returning an object from a client tool works at runtime but violates the published TS type**
    (`string | number | void`). `JSON.stringify` it yourself to keep the compiler quiet.
11. **Streaming/partial agent text does not arrive via `onMessage`** — tentative agent responses go
    to `onDebug`, and streaming parts to `onAgentChatResponsePart` (which must be enabled on the
    agent for voice conversations, per S7). A "live typing" transcript needs that event enabled.
12. **Barge-in corrupts an already-rendered transcript** unless you also handle
    `onAgentResponseCorrection` (§6.4).

### Could not confirm from primary ElevenLabs docs — confidence LOW

- **HTTPS / secure-context / localhost requirement.** Not documented anywhere I could find in the
  ElevenLabs docs (§9.2). The browser-platform requirement is real but was not verified against an
  ElevenLabs page in this task. Verify against MDN before treating it as an ElevenLabs constraint.
- **Whether `interruption` is in the default `client_events` set for a newly created agent.** S8 says
  it must be "a selected client event" but does not state the default. Check the dashboard on your
  actual agent.
- **The default value of `turn_eagerness`.** S8 lists `"patient" | "normal" | "eager"`; `"normal"`
  appears to be the default but the page did not state it outright.
- **Whether the `xi-api-key` header is formally required on `GET /v1/convai/conversation/token`.**
  S9's parameter table did not list required headers, though every code example in S2/S3 sends
  `xi-api-key` and minting plainly requires authentication. Treat as required.
- **`@elevenlabs/react-native` version and API.** Named in S14 but not investigated; out of scope for
  a browser build.
- **Agent-side `client_events` array literal syntax** for enabling `interruption` via API rather than
  the dashboard. Not captured; see S8 and the agent create/update API reference if you want agents as
  code.
- **The `allowlist` field's exact location in the agent config JSON** (S6 names the field but the
  fetched summary did not show a full config snippet).

### Pages identified but not fetched in depth (for follow-up)

- `https://elevenlabs.io/docs/eleven-agents/customization/tools/tool-configuration/tool-interruptions.md`
  — "Control whether users can interrupt the agent while a tool runs."
- `https://elevenlabs.io/docs/eleven-agents/customization/events/client-to-server-events.md`
- `https://elevenlabs.io/docs/eleven-agents/libraries/web-sockets.md` — raw protocol, if you ever
  bypass the SDK.
- `https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-signed-url.md` — the
  signed-URL API reference proper (facts in §8.3 came from S6 and S3 instead).
- `https://elevenlabs.io/docs/eleven-agents/guides/quickstarts/next-js.md` — fetched, summarized
  only; re-read if you want its full component listing.

---

## Independent verification (adversarial pass)

Verified: 2026-10-03, by a second agent, independently. **Nothing below was taken from the
researcher's cited URLs on trust.** Every artefact was re-fetched in this pass:

- The two npm packages were downloaded as **tarballs** (`registry.npmjs.org/@elevenlabs/react/-/react-1.16.0.tgz`,
  `.../client/-/client-1.26.0.tgz`) and extracted, so the `.d.ts` / `.js` quotes below are from the
  files npm actually ships, not from a CDN rewrite.
- npm metadata re-fetched from `https://registry.npmjs.org/@elevenlabs%2Freact`, `%2Fclient`,
  `@11labs%2Freact`, `@11labs%2Fclient`, `elevenlabs`, `@elevenlabs%2Felevenlabs-js`,
  `@elevenlabs%2Freact-native`.
- Docs re-fetched as `.md` from `elevenlabs.io/docs/...`, starting from `llms.txt`.
- **Two sources the first pass did not use**, which settle three of its open questions:
  - `https://elevenlabs.io/docs/eleven-agents/api-reference/agents/create.md` (S15) — the full agent
    config schema, with field types and **defaults**.
  - `https://elevenlabs.io/docs/api-reference/authentication.md` (S16) — the normative API-auth page.

**Headline: 29 of 32 claims CONFIRMED verbatim. 1 claim is partly REFUTED (#25 — the allowlist
shape is wrong and will break code). 2 claims are confirmed but mis-cited (#22, #31). The low-
confidence #27 is upgraded to CONFIRMED. The low-confidence #29 negative result stands.**

The researcher's 15 stated blockers all survive scrutiny. They were not over-claiming.

### Verdict table

| # | Status | Note |
|---|---|---|
| 1 | **CONFIRMED** | Strengthened — see below |
| 2 | **CONFIRMED** | |
| 3 | **CONFIRMED** | |
| 4 | **CONFIRMED** | Incomplete, not wrong — see below |
| 5 | **CONFIRMED** | Including the "stale docs page" charge |
| 6 | **CONFIRMED** | |
| 7 | **CONFIRMED** | Key-for-key, in order |
| 8 | **CONFIRMED** | |
| 9 | **CONFIRMED** | |
| 10 | **CONFIRMED** | |
| 11 | **CONFIRMED** | |
| 12 | **CONFIRMED** | One sub-quote mis-attributed to the `.d.ts` |
| 13 | **CONFIRMED** | |
| 14 | **CONFIRMED** | |
| 15 | **CONFIRMED** | Strengthened: `expects_response` **default is `false`** (S15) |
| 16 | **CONFIRMED** | |
| 17 | **CONFIRMED** | |
| 18 | **CONFIRMED but INCOMPLETE** | The real list has **15** system vars, not 4 |
| 19 | **CONFIRMED** | |
| 20 | **CONFIRMED** | |
| 21 | **CONFIRMED + REFINED** | It *is* automatic in text-only mode |
| 22 | **CONFIRMED, mis-cited** | And `CALLBACK_KEYS` is not importable where you'd expect |
| 23 | **CONFIRMED** | |
| 24 | **CONFIRMED** | Plus: `turn_eagerness` default **is** documented — `normal` |
| 25 | **PARTLY REFUTED** | **`allowlist` is an array of objects, not strings** |
| 26 | **CONFIRMED** | Exactly, field for field |
| 27 | **CONFIRMED (upgraded from LOW)** | S16 makes it normative |
| 28 | **CONFIRMED** | |
| 29 | **CONFIRMED (negative result stands)** | Re-grepped independently |
| 30 | **CONFIRMED** | |
| 31 | **CONFIRMED, mis-cited** | Quote lives on the JS SDK page |
| 32 | **CONFIRMED** | |

---

### Claim 25 — the one real error. Fix this before writing auth code.

The claim quotes two field descriptions as verbatim:
`enable_auth` = *"Activates signed URL requirement"* and `allowlist` = *"Array of approved
hostnames"*. **Neither string appears on the cited page** (`customization/authentication.md`) — I
grepped it for `Activates` (0 hits) and `Array of approved` (0 hits). They are paraphrases presented
as quotes.

The field **names** are real. Here are their actual definitions, verbatim from **S15**
(`https://elevenlabs.io/docs/eleven-agents/api-reference/agents/create.md`, section `AuthSettings`):

```
- `enable_auth` (boolean, optional, default: false) — If set to true, starting a conversation with an agent will require a signed token
- `allowlist` (list of AllowlistItem, optional) — A list of hosts that are allowed to start conversations with the agent
- `require_origin_header` (boolean, optional, default: false) — When enabled, connections with no origin header will be rejected. If the allowlist is empty, this option has no effect.
- `shareable_token` (string, optional) — A shareable token that can be used to start a conversation with the agent
```

and, verbatim:

```
### AllowlistItem

- `hostname` (string, required) — The hostname of the allowed origin
```

**-> `allowlist` is a list of OBJECTS `{ "hostname": "..." }`, not a list of strings.** Writing
`allowlist: ["letterlens.app"]` will fail validation. This also resolves the first pass's open
question about where the field lives in the config JSON. Verbatim from
`customization/authentication.md`:

```json
{
  "platform_settings": {
    "auth": {
      "enable_auth": false,
      "allowlist": [
        { "hostname": "example.com" },
        { "hostname": "app.example.com" },
        { "hostname": "localhost:3000" }
      ]
    }
  }
}
```

Note `localhost:3000` is given as a valid allowlist entry — so an allowlisted agent still works in
dev. The dashboard location is the **Security** tab (verbatim: "navigate to the **Security** tab"),
not the Advanced tab.

Everything else in claim 25 is **CONFIRMED verbatim**: the 15-minute expiry sentence, the 10-hostname
limit ("You can specify up to 10 unique hostnames that are allowed to connect to your agent"), exact
hostname matching with separate subdomain entries, and the `signed_url` response shape.

One correction to the first pass's *advice* (not a claim under test): section 8.1 recommends a public
agent plus allowlist as the hackathon path. The docs disagree — verbatim from
`customization/authentication.md`: "For client-side applications, signed URLs are the recommended
default."

---

### Claims confirmed with corrections or additions

**#1 — strengthened.** `dist/index.d.ts` line 1 is exactly `export * from "@elevenlabs/client";`.
Additional evidence the first pass did not cite: `@elevenlabs/react@1.16.0`'s own `package.json`
declares `"dependencies": {"@elevenlabs/client": "1.26.0"}` (an exact pin, not a range) and
`"peerDependencies": {"react": ">=16.8.0"}`. So the one-dependency claim is right, and the client
version you get is pinned — no float.

**#4 — incomplete, not wrong.** The provider props type and the `useRawConversationRef` error string
are verbatim. But the claim implies a single shared error message. There are **eight distinct
messages**, one per hook — grep of `dist/conversation/*.js`:

```
ConversationClientTools.js:77:  throw new Error("useConversationClientTool must be used within a ConversationProvider");
ConversationContext.js:24:      throw new Error("useRawConversationRef must be used within a ConversationProvider");
ConversationContext.js:38:      throw new Error("useRegisterCallbacks must be used within a ConversationProvider");
ConversationControls.js:122:    throw new Error("useConversationControls must be used within a ConversationProvider");
ConversationFeedback.js:40:     throw new Error("useConversationFeedback must be used within a ConversationProvider");
ConversationInput.js:51:        throw new Error("useConversationInput must be used within a ConversationProvider");
ConversationMode.js:36:         throw new Error("useConversationMode must be used within a ConversationProvider");
ConversationStatus.js:40:       throw new Error("useConversationStatus must be used within a ConversationProvider");
```

`useConversationClientTool` throwing matters: a tool-registering leaf component also needs the
provider. `useRawConversation` tolerating absence is confirmed verbatim from its docstring.

**#5 — confirmed, including the accusation against the docs.** `react.md` line 291, re-fetched today,
still reads verbatim:

```js
const conversationId = await conversation.startSession({
  agentId: "agent_7101k5zvyjhmfg983brhmhkd98n6",
  userId: "user_9302xkm82nds93", // optional field
});
```

The shipped type is `startSession: (options?: HookOptions) => void`. The docs page is stale. Lines
335 and 372 of the same page also `await conversation.startSession({...})` without using a return
value — harmless but misleading.

**#12 — one sub-quote mis-sourced.** The `livekitUrl`, `webRtc.singlePeerConnection` ("LiveKit's v1
join protocol") and `iceTransportPolicy` ("relay" / "on networks that drop direct UDP flows") quotes
are all verbatim in `client@1.26.0/dist/utils/BaseConnection.d.ts`, as cited. But the sentence "In
WebRTC mode the input format and sample rate are hardcoded to `pcm` and `48000` respectively" is
**not** in that `.d.ts` — it is `libraries/java-script.md` line 276. The *output* has its own
sentence at line 304. Content correct, citation wrong.

**#15 — strengthened, and the default confirms the blocker.** The dashboard wording, verbatim from
`tools/client-tools.md`: "When you want your agent to receive data back from a client tool, ensure
that you tick the **Wait for response** option in the tool configuration." Followed by: "Once the
client tool is added, when the function is called the agent will wait for its response and append the
response to the conversation context."

The API field, verbatim from **S15** — note the **default**:

```
- `expects_response` (boolean, optional, default: false) — If true, calling this tool should block the conversation until the client responds with some response which is passed to the llm. If false then we will continue the conversation without waiting for the client to respond, this is useful to show content to a user but not block the conversation
```

**`default: false`.** So the first pass's blocker is not just real, it is the *out-of-the-box*
behaviour: a freshly defined client tool ignores its own return value until you change this. The
claim's gloss ("false when no acknowledgment is needed") is a paraphrase; the real description is
above.

**#18 — confirmed but materially incomplete.** All four named variables exist. But
`personalization/dynamic-variables.md` lists **15**, and several are useful here:
`system__agent_id`, `system__current_agent_id`, `system__caller_id`, `system__called_number`,
`system__call_duration_secs`, `system__time_utc`, `system__time`, `system__timezone`,
`system__conversation_id`, `system__call_sid`, `system__call_id`, `system__agent_turns`,
`system__current_agent_turns`, `system__current_subagent_turns`, `system__is_text_only`,
`system__conversation_history`. Verbatim: "Custom dynamic variables cannot use the reserved
`system__` prefix." The Python `ConversationInitiationData(dynamic_variables=...)` form is confirmed.

Also missed by the first pass, and useful for testing a prompt before wiring real values — verbatim:
"Set `conversation_config.agent.dynamic_variables.dynamic_variable_placeholders`. Each key is the
variable name; the value is the placeholder used during testing."

**#21 — confirmed and refined.** `handleTentativeAgentResponse` -> `onDebug` is verbatim. But the
claim overstates the gating. Verbatim from `events/client-events.md`, under
`agent_chat_response_part`:

> * Streams the agent's response text as it is generated, as `start`, `delta` and `stop` messages
> * **Always sent in text-only mode**; in voice conversations it must be explicitly enabled in the agent's `client_events` configuration
> * Not sent while the agent or an active procedure uses a blocking guardrail, which has to evaluate the whole response before any of it is released
> * `response_id` identifies the message being streamed and matches the `response_id` of the `agent_response` that later commits it

Two things the build needs: it is free in text-only mode, and the last bullet is the **documented
join key** for reconciling streamed parts against the final `agent_response` — exactly the problem
the first pass flagged as blocker #8 but solved only by guesswork ("reconcile using
`response_id`/`event_id`"). The docs state the contract.

**#22 — confirmed, and stronger than claimed, but mis-cited twice.**

Composition is real and goes further than "the React SDK composes": the *client's* own
`mergeOptions` does it. Verbatim from `client@1.26.0/dist/utils/mergeOptions.d.ts`:

```
 * Merges multiple partial option objects into one.
 *
 * - Plain objects are deep-merged so that later configs can override
 *   individual nested fields without wiping unrelated ones.
 * - Functions sharing the same key are composed: all are called in
 *   order (earliest config first) with the same arguments.
 * - All other values are shallow-merged (last value wins).
```

and the implementation, verbatim:

```js
            else if (typeof accVal === "function" && typeof objVal === "function") {
                result[key] = ((...args) => {
                    accVal(...args);
                    objVal(...args);
                });
            }
```

The provider's merge order, verbatim from `ConversationProvider.js`:

```js
const sessionOptions = mergeOptions({ livekitUrl: calculatedLivekitUrl }, defaultConfig, stableCallbacks, listenerMap.compose(), options ?? {}, { origin });
```

**-> A consequence the first pass missed, and it is a trap:** because same-key functions are
*composed and never replaced*, you **cannot override a provider-level callback at `startSession`
level**. Both fire, provider first. If LetterLens puts a default `onMessage` on the provider and a
per-session `onMessage` on `startSession`, every message is handled **twice**. Pick one level per
callback.

Two citation errors:

- The comment "Used by the React SDK to pre-initialize listener maps for callback composition" is in
  `@elevenlabs/client@1.26.0/dist/types.d.ts` (above `CALLBACK_KEYS`), **not** in react's
  `ConversationProvider.js`.
- **`CALLBACK_KEYS` is not importable from `@elevenlabs/client` or `@elevenlabs/react`.** The
  provider imports it from `"@elevenlabs/client/internal"`. The client's public `index.d.ts`
  re-exports only *types* from `BaseConversation.js`, and `CALLBACK_KEYS` is a runtime value, so
  `export * from "@elevenlabs/client"` in react's index does not carry it. Confirmed against
  `package.json` `exports`: `"./internal": "./dist/internal.js"`. If you want it, import
  `{ CALLBACK_KEYS } from "@elevenlabs/client/internal"` — an undocumented subpath, so do not build
  on it.

**#24 — confirmed, and one of the first pass's open questions is closed.** Both quotes are verbatim
at `conversation-flow.md` lines 344 and 346, and the 1-30s range for `turn_timeout` is verbatim
("must be between 1 and 30 seconds"). The first pass listed the `turn_eagerness` default as
unresolved. **S15 documents it.** Verbatim:

```
- `turn_timeout` (double, optional, default: 7) — Maximum wait time for the user's reply before re-engaging the user
- `turn_eagerness` (enum, optional, default: normal) — Controls how eager the agent is to respond. Low = less eager (waits longer), Standard = default eagerness, High = more eager (responds sooner)
  - Allowed values: `patient`, `normal`, `eager`
```

So: `turn_timeout` default **7** seconds, `turn_eagerness` default **`normal`**. (The description's
"Low/Standard/High" wording is inconsistent with the `patient/normal/eager` enum values — a docs bug;
use the enum values.)

**#27 — upgraded from LOW to CONFIRMED.** The claim's own hedge ("The API-reference parameter table
did not itself list required headers") is correct — I re-fetched `get-webrtc-token.md` and it has no
header section at all. But the first pass stopped one page too early. **S16**
(`https://elevenlabs.io/docs/api-reference/authentication.md`) is normative, verbatim:

> The ElevenLabs API uses API keys for authentication. **Every request to the API must include your
> API key**, used to authenticate your requests and track usage quota.

> All API requests should include your API key in an `xi-api-key` HTTP header as follows:

```bash
xi-api-key: ELEVENLABS_API_KEY
```

> **Remember that your API key is a secret.** Do not share it with others or expose it in any
> client-side code (browsers, apps).

The code-comment quote in the claim is also verbatim (`java-script.md` lines 122-124). **Treat
`xi-api-key` as documented-required, not inferred.** S16 also mentions API-key **IP allowlisting**
(non-allowlisted IPs rejected with `403`) — worth knowing if token minting suddenly 403s from a
deploy platform with rotating egress IPs.

**#29 — the negative result stands, independently reproduced.** `llms.txt` is 1374 lines today. My
own grep for `microphone|permission|https requirement|secure context|localhost` returned exactly one
page: `help-center/troubleshooting/how-can-i-make-sure-my-microphone-is-working.md`. I fetched it.
It covers Windows privacy settings and Chrome per-site permission toggles only — **no statement about
HTTPS, secure contexts, or localhost.** So: confirmed, there is no ElevenLabs-documented
secure-context requirement. (I also tried `llms-full.txt` to grep the whole corpus at once; it
returns a 15-byte `Redirecting...` stub, so corpus-wide grep is not available that way. Noting it so
nobody wastes time on it.) Treat the secure-context rule as a browser platform fact, cited to MDN,
not to ElevenLabs.

**#31 — confirmed, quote is on a different page than cited.** The quote is verbatim, but at
`libraries/java-script.md` lines 166-168 — **not** `events/client-events.md`. (The first pass's own
section 6.6 attributed it correctly to S3; the claim statement regressed.) The four named events are
each confirmed on `client-events.md` with "Must be explicitly enabled in the agent's `client_events`
configuration".

**And this closes another open question.** The first pass could not find the `client_events` array
literal syntax for enabling events via API. **S15 has the complete enum**, verbatim:

```
- `client_events` (list of enum, optional) — The events that will be sent to the client
  - Allowed values: `conversation_initiation_metadata`, `asr_initiation_metadata`, `ping`, `audio`, `interruption`, `user_transcript`, `tentative_user_transcript`, `agent_response`, `agent_response_correction`, `client_tool_call`, `mcp_tool_call`, `mcp_connection_status`, `agent_tool_request`, `agent_tool_response`, `agent_tool_response_full_payload`, `agent_response_metadata`, `vad_score`, `agent_chat_response_part`, `client_error`, `guardrail_triggered`, `dtmf_request`, `agent_response_complete`, `context_usage`, `internal_turn_probability`, `internal_tentative_agent_response`
```

So agents-as-code is possible: set `conversation_config.client_events` to include `interruption`,
`agent_response_correction`, `agent_chat_response_part`, `user_transcript`, `agent_response`, `audio`.

**Still unresolved, as the first pass said:** the schema marks `client_events` `optional` with **no
documented default list**, so whether `interruption` ships enabled on a new agent remains
**UNVERIFIABLE from docs**. Check the dashboard. The first pass was right to flag it.

---

### What the first pass MISSED that the build will need

Found while verifying; none of these are in the note above.

**1. Conversations hard-stop at 10 minutes by default.** Verbatim from S15:

```
- `max_duration_seconds` (integer, optional, default: 600) — The maximum duration of a conversation in seconds
```

A LetterLens demo that walks through a long letter will be cut off at 600s with no code-level warning.
Raise it on the agent before demo day.

**2. Double-fired callbacks.** See #22 above. Provider-level and `startSession`-level callbacks are
**composed, not overridden**. Put each callback at exactly one level.

**3. `onConversationCreated` / `ConversationLifecycleOptions`.** Present in
`client/dist/BaseConversation.d.ts` and in react's `HookOptions`, unmentioned by the first pass:

```ts
export type ConversationCreatedCallback = (conversation: Conversation) => void;
```

It hands you the `Conversation` instance as soon as it exists — earlier than `onConnect`. The
provider consumes it internally. Verified in `ConversationProvider.js`: the provider builds
`providerLifecycleOptions` for `onConversationCreated`, `onConnect`, `onDisconnect` and
`onStatusChange` and **spreads them over** your options (`{...sessionOptions, ...providerLifecycleOptions}`,
a plain spread, *not* `mergeOptions`) — but each wrapper re-invokes yours
(`sessionOptions.onConnect?.(props)`, `userOnDisconnect?.(details)`,
`sessionOptions.onStatusChange?.(props)`, `userOnConversationCreated?.(conv)`). So your four
lifecycle callbacks still fire, just after the provider's bookkeeping. They are the four exceptions
to the double-fire rule in item 2.

**4. Status `"disconnecting"` is where the provider releases the conversation.** Verbatim comment
from `ConversationProvider.js`, relevant to the two-enum gotcha in #9:

```js
        // "disconnecting" marks the moment the session stops being usable, on
        // every path (agent hangup, raw endSession(), provider endSession()) —
        // release the conversation here so it clears in the same React batch
        // as the status transition, and consumers never observe a live status
        // with a released conversation (or vice versa).
```

So the client-level `"disconnecting"` is not merely "swallowed" by React — it is the trigger the
React layer uses. `useRawConversation()` goes `null` at that moment.

**5. Data-residency base URLs for token minting.** `get-webrtc-token.md` lists servers the note's
section 8 does not mention:

```
- `https://api.elevenlabs.io` (Production, default)
- `https://api.us.elevenlabs.io` (Production US)
- `https://api.eu.residency.elevenlabs.io` (Production EU)
- `https://api.in.residency.elevenlabs.io` (Production India)
- `https://api.sg.residency.elevenlabs.io` (Production Singapore)
```

If the workspace is on EU/India/Singapore residency, minting against `api.elevenlabs.io` will fail.
Pair this with `serverLocation` on `HookOptions`.

**6. `participant_name` defaults to the user ID.** Verbatim: "Optional custom participant name. If
not provided, user ID will be used."

**7. `require_origin_header` in `AuthSettings`** (see #25). Verbatim: "When enabled, connections with
no origin header will be rejected. If the allowlist is empty, this option has no effect." This is the
knob that makes an allowlist meaningfully enforceable.

**8. Turn-taking options worth a look for a reading-aloud agent**, all from S15's `TurnConfig`:

```
- `initial_wait_time` (double, optional) — How long the agent will wait for the user to start the conversation if the first message is empty. If not set, uses the regular turn_timeout.
- `silence_end_call_timeout` (double, optional, default: -1) — Maximum wait time since the user last spoke before terminating the call
- `spelling_patience` (enum, optional, default: auto) — Controls if the agent should be more patient when user is spelling numbers and named entities. Auto = model based, Off = never wait extra
- `speculative_turn` (boolean, optional, default: false) — When enabled, starts generating LLM responses during silence before full turn confidence is reached, reducing perceived latency. May increase LLM costs.
- `retranscribe_on_turn_timeout` (boolean, optional, default: false) — When enabled, if VAD detects no speech, attempts to re-transcribe accumulated audio at turn timeout. Disables silence discount billing for affected turns.
```

`speculative_turn` is the cheap latency win for a demo. `spelling_patience` matters if users read
reference numbers off a letter.

**9. `agent_response_correction` must itself be in `client_events`.** The first pass's blocker #8
(barge-in corrupts the transcript) depends on a callback whose event is in the gated enum (item under
#31). So that blocker has a **dashboard prerequisite the first pass did not state**: without
`agent_response_correction` selected, `onAgentResponseCorrection` never fires and the transcript stays
wrong with no way to detect it. Enable `interruption` **and** `agent_response_correction` together.

**10. `@elevenlabs/react-native` is at `1.2.28`** (published 2026-09-29T13:02:26.241Z), with the same
`next` = `1.0.0-rc.1` trap. Listed as "not checked" in section 1 above. Out of scope for the browser
build, recorded for completeness.

**11. TTS override model enum**, if section 5.1's `overrides.tts` is ever used — from S15:
`eleven_turbo_v2`, `eleven_turbo_v2_5`, `eleven_flash_v2` (default), `eleven_flash_v2_5`,
`eleven_multilingual_v2`, `eleven_v3_conversational`, `eleven_v4`, `eleven_v4_turbo`. The first pass
left `overrides.tts.voiceId` with no model list.

### Sources added by this pass

| # | Source | URL |
|---|---|---|
| S15 | **Create agent (API ref)** — full agent config schema with defaults | https://elevenlabs.io/docs/eleven-agents/api-reference/agents/create.md |
| S16 | **API Authentication** — normative `xi-api-key` requirement | https://elevenlabs.io/docs/api-reference/authentication.md |
| S17 | Microphone troubleshooting (checked for a secure-context statement; has none) | https://elevenlabs.io/docs/help-center/troubleshooting/how-can-i-make-sure-my-microphone-is-working.md |
| S18 | npm tarballs, extracted and read directly | https://registry.npmjs.org/@elevenlabs/react/-/react-1.16.0.tgz and https://registry.npmjs.org/@elevenlabs/client/-/client-1.26.0.tgz |

**S15 is the most valuable page neither pass started from.** It is the single authoritative list of
agent-config field names, types and defaults, and it answered three questions the first pass left
open. Read it before touching agent configuration.
