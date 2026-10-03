# LetterLens — demo-day operations notes

**What this file is.** `docs/submission.md` Section B has the demo script and a one-line-per-
segment "if it breaks" table, and it says: *"Deeper failure-mode analysis and recovery procedures
live in `docs/demo-notes.md` — read that before the event; do not try to debug from this table."*
This is that file.

**So this file does not repeat the script.** It covers the four things that decide whether the
script survives contact with a real room: whether the room can read the screen, whether the camera
can read the paper, what to do when the network dies, and whether the demo meets the accessibility
bar its own product promises. Section 5 is a timed runbook that sits *underneath* the script in
Section B.

Read this **before** the event. On the day, you want Section 5 printed and Section B in your hand.

Written 2026-10-03 against commit `39b8655`, then revised the same day against
`docs/research/08-gemma-live-api-test-results.md` — **live HTTP testing against a real API key**,
which overturned the model pin — twice, §2 then §§6.1/10 — and which, contrary to its own first
reading, left the 8-second latency budget standing
for this file. The revised material is §§0.1–0.4, 3.1a, and the marked passages in §§1.5, 2.4, 3.1,
3.3, 4.5, 5 and Appendix A. **Where this file and the docs-based notes 01 and 07 disagree, note 08
wins.**

**Revised again 2026-10-03, this time against the working tree rather than against research notes.**
The backend and frontend now exist and have been exercised end to end. Two premises this file was
built on are gone, and one number changed:

- **There is no tunnel.** `[REPO]` `read_document` is an ElevenLabs **client** tool
  (`agent/tools/read_document.json`: `"type": "client"`), so the *browser* calls the backend
  directly — `frontend/src/App.tsx` does a template-literal `fetch` of `${BACKEND}/read_document` with
  `BACKEND = import.meta.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000"` — and ElevenLabs' cloud
  never reaches the laptop. `ngrok`, `cloudflared`, `PUBLIC_BASE_URL` and `TOOL_WEBHOOK_SECRET` are
  **not used by this MVP at all**. Every tunnel instruction below is dead; it is struck out or
  rewritten. Treat this as a demo-risk **win** and say it plainly: a tunnel is a thing that dies
  quietly mid-demo, and there is no longer one to die.
- **There is one tool, not six.** `[REPO]` Built and working: **`read_document`** (client). `App.tsx`
  registers exactly `clientTools: { read_document: readDocument }`; `backend/app.py` exposes exactly
  `/health`, `/signed-url` and `/read_document`. **NOT BUILT:** `draft_reply`, `add_event`,
  `set_reminder` — no endpoint, no client-tool registration, no `.ics` generation, no calendar card,
  no reminder card. `end_call` and `skip_turn` are native ElevenLabs system tools needing no code,
  but no file in the repo shows them configured. Anything below that treats the unbuilt three as
  working features is now marked **NOT BUILT**.
- **The user-visible read is ~8 seconds, not 3.7–4.5.** Note 08 §10's 3.7–4.5 s is the *raw model
  call*. Measured end to end through the running backend on 2026-10-03: **8.1 s, 7.6 s, 8.7 s**,
  HTTP 200 on the first attempt for all three letters. §0.2 has the tail and the abandon time, which
  is now **35 s**, not 15.

## Provenance legend

Every non-obvious claim is tagged. Do not treat an unverified tag as fact.

| Tag | Means |
|---|---|
| `[REPO]` | Read directly out of this repository. Reproducible by anyone. |
| `[RESEARCH]` | From `docs/research/*.md`, which cite primary sources re-fetched 2026-10-03. |
| `[WEB]` | Looked up on the open web during this pass, cited inline. |
| `[CALC]` | Arithmetic done here from stated assumptions. The assumption is always stated; check it. |
| `[PRACTICE]` | General AV / accessibility / demo practice. Sensible, widely done, **not verified against a source in this pass.** |
| `[UNVERIFIED]` | A specific claim I could not confirm. Confirm before relying on it. |

---

## 0. What exists right now, and the four things that kill the demo outright

> **⚠️ SUPERSEDED as written at commit `39b8655`.** That version of this section said `App.tsx` was
> the unmodified Vite starter, `backend/` held only `requirements.txt`, and `agent/*.json` did not
> exist. All three are now false — the MVP is built. The inventory below replaces it.

`[REPO]` What exists in the working tree on 2026-10-03:

- **`backend/app.py`** — FastAPI, three routes and no more: `GET /health` (reports which keys
  loaded), `GET /signed-url` (mints a short-lived ElevenLabs conversation token so
  `ELEVENLABS_API_KEY` never reaches the browser), `POST /read_document` (one camera frame in,
  `{"text": ..., "elapsed_s": ...}` out). No webhook handlers, because there are no webhook tools.
- **`frontend/src/App.tsx`** — camera, conversation UI, and `clientTools: { read_document:
  readDocument }`. It fetches `/signed-url` and posts frames to `/read_document` on
  `http://127.0.0.1:8000` by default.
- **`agent/tools/read_document.json`** — the one tool. `"type": "client"`,
  `expects_response: true`, `response_timeout_secs: 120`, `pre_tool_speech: "force"`,
  `tool_call_sound_behavior: "always"`, `interruption_mode: "allow"`, and **no parameters** — it
  reads whatever the camera sees now.
- **NOT BUILT:** `draft_reply`, `add_event`, `set_reminder`, and therefore no `.ics` file, no
  calendar card and no reminder card. Do not demo them and do not keep a recovery step for them.
- **What `read_document` actually returns:** not the nine-field structured object in
  `skills/letter-reader/references/output-schema.md`. `backend/app.py` returns `{"text": ...,
  "elapsed_s": ...}` where the text is at most six plain lines — `FROM:`, `ABOUT:`, `WHEN:`,
  `DEADLINE:`, `REF:`, `CONTACT:`, each with a value or `NONE` — and the agent summarises that in
  its own voice. **The structured-object contract in `output-schema.md` is aspirational, not
  implemented.**

So §1 and §4 below are still **requirements to build against** rather than an audit — the UI exists
but has not been audited against them. §2 and §3 are real right now, because the printed paper and
the venue network do not care how finished the app is.

### 0.1 The model pin — **FIXED**

`[REPO]` `.env.example` now pins `GEMMA_MODEL=gemma-4-26b-a4b-it` and
`GEMMA_VISION_MODEL=gemma-4-26b-a4b-it`, with an inline head-to-head citing
`docs/research/08-gemma-live-api-test-results.md` §§6.1 and 10 — vision is verified on that ID
against all three letters in `test-letters/`. `LLM_TIMEOUT_MS=8000` is unchanged. The two
split-path lines (`#CHAT_MODEL=gemini-2.5-flash-lite`, `#VISION_TIMEOUT_MS=90000`) are still in
the file but are marked **no longer needed** and must stay commented out.

**What it used to be, and why it mattered.** Both values were `gemma-3-27b-it`. `[RESEARCH]` Note 08
§2 records the live result: a flat **404**, verbatim *"models/gemma-3-27b-it is not found for API
version v1beta, or is not supported for generateContent"*. The repo's defaults could never have
worked on any request. Earlier drafts of this file and of `docs/submission.md` said the fix was
`gemma-4-31b-it`, on the strength of the §3 vision call; **that is superseded.** Note 08 §6.1 removed
the `maxOutputTokens: 1` confound with a serial cross at concurrency 1 — `gemma-4-26b-a4b-it`
answered **8/8 in a 2.0 s median** with thinking active and output uncapped, while `gemma-4-31b-it`
took **24.9 s** on a single capped token — and §10 then read all three letters on 26b in
**3.7–4.5 s, 3/3 first attempt, verbatim-correct**. Note 01's recommendation was right for the right
reason. `gemma-4-31b-it` remains useful only as a second 30 RPM quota bucket, since the free tier is
scoped per project *per model*.

**What was still open is now closed.** ✅ The application path has been exercised: `POST
/read_document` against the running backend with the full-resolution PNGs in `test-letters/`
returned **HTTP 200 on the first attempt for all three letters, in 8.1 s, 7.6 s and 8.7 s**, every
field verbatim-correct against the known-good `.txt` transcripts. The demo-day consequence of a bad
pin has not changed, though: `read_document` would fail on every single attempt, in a way that looks
exactly like a network failure from the stage, and you would burn the whole "if it breaks" budget on
a problem no amount of re-holding the letter can fix. **So still get one real 200 through the backend,
with a real frame, at T-60.** Item 1 in the T-60 checklist. Per instruction I did not read or touch
`.env.local` — check the pin there too.

`[REPO]` **One correction to the sentence above about `LLM_TIMEOUT_MS=8000`.** It is still in
`.env.example`, but **`backend/app.py` never reads it**, and that is correct rather than an
oversight: a *healthy* end-to-end read exceeds 8 s (8.1–8.7 s measured), so an 8-second gate would
kill good reads. The vision call is bounded by the backend's own
`httpx.Timeout(60.0, connect=10.0)`. Do not "fix" this by wiring `LLM_TIMEOUT_MS` into the vision
path.

`[REPO]` Two good signs already in `.gitignore`: `captures/` and `latency-*.jsonl`. **Ship the
latency log.** The model call is 3.7–4.5 s (§0.2), but that figure excludes base64 encoding, the
upload of a ~0.5 MB frame, retries and TTS — which is exactly why the measured end-to-end figure is
~8 s. The log is what tells you at T-60 what tonight's distribution looks like, rather than finding
out mid-script.

### 0.2 The read is ~8 seconds, with a tail — and here is the number to rehearse against

`[RESEARCH]` + `[REPO]` This section was once the biggest risk in the document. It is now a managed
one, and the reason is worth knowing: the alarming figures belonged to one model. Note 08 is **live
HTTP against a real key**; the measured end-to-end row is **live HTTP against the running backend**.
Everything below came off the wire on 2026-10-03.

| Measurement | Value |
|---|---|
| **End to end, `POST /read_document`, all three letters in `test-letters/`** | **8.1 s, 7.6 s, 8.7 s — HTTP 200 first attempt 3/3, verbatim-correct** |
| **The tail, five consecutive calls** (recorded in `backend/app.py`'s own comments) | **5.1, 5.5, 8.2, 14.4, 30.5 s** |
| Raw model call only, vision, on the pinned `gemma-4-26b-a4b-it` | 3.7–4.5 s (note 08 §10) — **a component, not the user-visible figure** |
| Raw model call only, text, serial, 8 calls, thinking active, output uncapped | 2.0 s median, max 2.5 s, 8/8 (§6.1) |
| Failures across note 08 §§6.1 and 10 | 0 in 19 calls |
| 40 requests at 8-way concurrency | 33×200, 7×429, **0×500** (§1.1) |
| Rejected alternative, `gemma-4-31b-it` | 20–57 s, ~50 % serial failure rate, 36.8–56.8 s on vision (§§6, 10) |

**Budget ~8 seconds per read.** The gap between the 3.7–4.5 s model call and the ~8 s the presenter
actually waits is base64 encoding and the upload of a ~0.5 MB frame — real work that happens before
the model sees anything. **Quote 8 s, never 3.7–4.5 s, as the user-visible number.**

**And read the tail row again, because it is the one that matters on stage.** 5.1, 5.5, 8.2, 14.4,
30.5 s across five consecutive calls is a *tail* problem, not an average one. The mean is reassuring
and the 95th percentile is what the room sees. **So: ten seconds of silence is normal, and demo-day
abandon time is 35 seconds.**

Three consequences, in order of how much they change the plan:

1. **`LLM_TIMEOUT_MS=8000` must NOT gate the vision path**, because a *healthy* read exceeds it.
   `backend/app.py` is already correct here — it never reads the variable and bounds the call with
   its own `httpx.Timeout(60.0, connect=10.0)`. Note 08 §7 **option 1, split the paths, is
   superseded by §10 and must not be built**: one Gemma model serves both paths. The spoken *"let me
   read that for you, one moment"* stays, and at ~8 s it is earning its keep as latency cover as
   well as accessibility. Containment holds either way: `read_document` is the only path to the
   letter, so a failed read degrades **one feature** instead of the whole conversation, and the agent
   can still talk to you and apologise.
2. **A long silence is the normal case for the first ten seconds, and a symptom after thirty-five.**
   You want the discriminators in §3.1a, and a pre-agreed abandon time — **set it at 35 s.** Earlier
   drafts said 75 s (from `gemma-4-31b-it`) and then 15 s (from the model-call figure). Both are
   wrong: 15 s would abandon a read that was going to land.
3. **Retries are still mandatory, and they are affordable but not free.** 26b went **19/19** across
   note 08 §§6.1 and 10 with no 5xx, and took 40 requests at 8-way concurrency with zero 500s
   (§1.1), so budget for 429s rather than failures. But a retry costs you another ~8 s, not four —
   so **take one and move on.**

`[RESEARCH]` Two mechanical rules the backend must follow, both from note 08 §§1.1 and 6, both of
which affect what you see on stage: **send requests strictly serially** (concurrency manufactures
500s rather than throughput), and **honour the `RetryInfo.retryDelay` in a 429 as a floor, not a
wait time** — one 429 advertised 17 s and the real recovery took 22.8 s.

### 0.3 The agent will read its own notes aloud unless the backend stops it

`[RESEARCH]` Note 08 §4. Both Gemma 4 models are thinking models, and the response arrives as **two
parts**:

```
parts[0] = { "text": "<reasoning>", "thought": true }
parts[1] = { "text": "<the actual answer>" }
```

On the measured vision call, `parts[0]` was **4,236 characters / 1,109 thought tokens** of visible
self-correction — verbatim, *"Wait, maybe they want the first sentence of the message?"* — and
`parts[1]` was **five tokens**. The obvious extraction, `candidates[0].content.parts[0].text`,
returns the scratchpad.

**Why this is a live-demo hazard and not a backlog item.** LetterLens is a voice product. If the
scratchpad reaches the agent, **the agent reads the model's entire deliberation aloud** — four
thousand characters of it, to a room, in a demo of an assistive product for blind people, having
promised "two or three short sentences, under forty words". It will not look like a bug. It will
look like the product working badly, which is worse. And a blind user has no way to see that what
they are hearing is deliberation rather than their letter.

The backend rule is three lines (note 08 §4):

```python
def answer_text(body: dict) -> str:
    parts = body["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))
```

`[RESEARCH]` **Streaming does not save you — it makes it arrive sooner.** Note 08 §8.1 confirms
`streamGenerateContent?alt=sse` works on Gemma (undocumented, and absent from
`supportedGenerationMethods`), and records that **the first SSE chunk is the reasoning, not the
answer.** A streaming voice UI that speaks tokens as they arrive would begin reading the
deliberation aloud immediately. Any streaming consumer must filter per chunk on the `thought` flag
and emit nothing until the first non-thought part.

**On the day:** if this happens, no retry fixes it and no amount of re-holding the letter fixes it —
the bug is in the backend. Interrupt the agent (barge-in is right there), say one honest line, and
go to the recording. §5.3 has the wording.

### 0.4 Structured output returns 200 and ignores you

`[RESEARCH]` Note 08 §5. Sending `responseMimeType: "application/json"` with a `responseSchema` to
`gemma-4-31b-it` returns **HTTP 200, not 400** — and the body comes back as markdown-fenced JSON
with a leading space and a trailing ` ``` `. The extraction is conceptually correct; `json.loads()`
on it raises. The schema is accepted and silently not honoured.

**Demo relevance:** this surfaces as `read_document` throwing on a *successful* model call, i.e. a
failure that looks identical to the network ones in §3 but happens on a perfectly good read, and
which a retry will reproduce roughly as often as not depending on whether the model felt like
fencing its output. The backend must strip fences before parsing and validate the shape server-side
regardless. Note 01's recommended alternative — function calling — is **verified working** in note
08 §8.4 (one declared `functionDeclarations` tool, clean typed args, no fence), so it is the better
target than fence-stripping if there is time before demo day. Note that §8.4 let the model *choose*
the tool; forcing it via `tool_config` is untested on Gemma, so keep a text-response fallback.

---

## 1. Projector legibility

### 1.1 Minimum text size

The derivation, so you can argue with the assumptions rather than the number.

`[PRACTICE]` The classic AV rule of thumb puts the farthest viewer at about **6× the projected image
height** for content that must be read (the "4/6/8 rule"; its modern successor is ANSI/InfoComm
DISCAS, which I did not verify here). Call that `D = 6H`.

`[PRACTICE]` Threshold acuity (the 20/20 line) is about 5 arcminutes per character. Comfortable
glance-reading of projected text for a mixed audience needs roughly **16–20 arcminutes**.

`[CALC]` At `D = 6H` and 20 arcmin (0.00582 rad), required cap height = `6H × 0.00582 = 0.035H`.
For a typical sans-serif, cap height ≈ 0.70 × font-size, so **font-size ≈ 0.050H — 5% of image
height.** At the relaxed 16 arcmin it is 4.0%. The projected image is a scaled copy of your
viewport, so percent-of-image-height = percent-of-viewport-height.

**Measure these in fullscreen (F11).** A maximised Chrome window at 1080p has roughly 950 px of
viewport, not 1080, so `vh` means something different windowed.

| Element | Target | @ 1280×720 fullscreen | @ 1920×1080 fullscreen |
|---|---|---|---|
| Agent transcript / caption — the thing the room reads | **6.5 vh** | 47 px | 70 px |
| Body text, status labels, key facts on the letter card | **5 vh** (floor 4 vh) | 36 px (floor 29 px) | 54 px (floor 43 px) |
| Secondary / supporting text | **3 vh** | 22 px | 32 px |
| Nothing below | **2.5 vh** | 18 px | 27 px |
| Focus ring thickness | **≥ 0.4 vh** | 3 px | 4 px |

`[REPO]` **The scaffold is roughly 3× too small.** `frontend/src/index.css` sets `font: 18px/145%`
on `:root`, dropping to `16px` at `max-width: 1024px`. 18 px at 1080p fullscreen is **1.7 vh** —
about a third of the 5 vh floor. `#root` is also `width: 1126px` with `border-inline`, so on a
1920-wide projector you get a narrow centred column with dead bands either side.

`[PRACTICE]` **Sizing-unit trap.** If you author literally in `vh`, `Ctrl` `+` will **not** enlarge
anything — browser zoom shrinks the CSS viewport, so `vh` elements keep the same physical size.
Author in `rem` off an `html` font-size and treat the `vh` figures as acceptance criteria you
measure. That keeps `Ctrl` `+` available as the on-stage escape hatch.

`[PRACTICE]` Cheapest route to a projector-legible build without restyling everything: one
`html { font-size: … }` override behind a `?demo=1` query flag, so the normal app keeps its normal
scale. *(Recommendation only — the human owns all CSS.)*

### 1.2 Contrast that survives a washed-out projector

WCAG 2.2 SC 1.4.3 Contrast (Minimum) AA is **4.5:1** for normal text, **3:1** for large text
(≥18 pt, or ≥14 pt bold). SC 1.4.11 Non-text Contrast is **3:1** for UI components and focus
indicators. `[PRACTICE — standard spec numbers, not re-verified this pass]`

**Why 4.5:1 is not enough on a projector.** A projector in a lit room cannot make black. Ambient
light adds a roughly constant luminance `a` to *both* foreground and background:

```
projected_ratio = (L_bg + a + 0.05) / (L_fg + a + 0.05)
```

`[CALC]` With a washed-out-room assumption of **a = 0.15** — my assumption, a model not a
measurement; a dark room is nearer 0.02, a bad one worse than 0.15:

| Measured on the laptop | Projects to (a = 0.15) | Verdict |
|---|---|---|
| 21:1 (`#000` on `#fff`) | **6.0:1** | Safe |
| 17:1 (`#1a1a1a` on `#fff`) | **5.7:1** | Safe |
| 12:1 (`#3d3d3d` on `#fff`) | **4.8:1** | Marginal pass |
| 7:1 | **4.0:1** | Fails AA on screen |
| 4.5:1 (bare AA) | **3.6:1** | Fails AA on screen |

**Target ≥ 12:1 measured for anything the room must read, ≥ 17:1 for the caption line.** Treat
4.5:1 as the legal floor for the shipped product, not the demo target.

`[REPO]` **Three contrast problems already in the scaffold.** Ratios computed here from the hex
values in `frontend/src/index.css`:

| Token | Pair | Measured | Projected (a=0.15) | Problem |
|---|---|---|---|---|
| `--text: #6b6375` on `--bg: #fff` | body, light mode | **5.73:1** | **3.6:1** | Passes AA on a laptop, fails on the projector. Use `#1a1a1a` or `#111`. |
| `--accent: #aa3bff` on `#fff` | accent | **4.39:1** | **3.1:1** | **Already fails WCAG AA (4.5:1) for normal-size text today**, before any projector. Only clears the 3:1 large-text / non-text bar. |
| `--text: #9ca3af` on `--bg: #16171d` | dark mode | **7.04:1** | **2.70:1** | Catastrophic on a projector. |

`[REPO]` **Dark mode will ambush you.** `index.css` declares `color-scheme: light dark` and a full
`@media (prefers-color-scheme: dark)` block. If the demo laptop is in Windows "Dark" app mode the
page flips to that 7:1 palette, which projects at **2.7:1**. `[PRACTICE]` A projector in a lit room
also renders a dark background as flat dirty grey with visible light leak, and bright text on it
blooms. **Set Windows app mode to Light, and ideally force a light theme for the demo view
regardless of OS preference.** There is a second reason in §2.1: a light screen is free fill light
on the paper.

### 1.3 Browser chrome, cursor, dev overlays

`[PRACTICE]` unless tagged.

- **Present a production build, not the dev server.** `npm run build && npm run preview`. The Vite
  dev server throws a full-screen red HMR overlay on any error, and React 19 `StrictMode`
  double-invokes effects.
  - `[RESEARCH]` The double-invoke is probably harmless for the voice session specifically: note 04
    §3.4 records that `startSession` is idempotence-guarded — "double-clicking 'Start' is safe and
    silently no-ops". It is **not** harmless for a camera effect or a fetch.
  - `[REPO]` **Gotcha:** `vite preview` serves on port **4173**, but `.env.example` sets
    `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`. Add 4173 to `CORS_ORIGINS` in your
    `.env.local`, or run preview with `--port 5173`. Discovering this live, as a silent CORS
    failure, is a very plausible way to lose the demo.
- **Fullscreen, no chrome:**
  `chrome.exe --app=http://localhost:5173 --start-fullscreen --user-data-dir="C:\demo-profile"`.
  `--app=` removes the omnibox — so no URL appears on the projector — and the tab strip.
- **Use a persistent dedicated profile, created at home.** A fresh `--user-data-dir` has **no stored
  microphone permission**, so you get a permission dialog live on stage — which `docs/submission.md`
  Section B already lists as a thing that "eats five seconds". Create `C:\demo-profile` beforehand,
  grant mic and camera once, turn the bookmarks bar off (`Ctrl` `Shift` `B`), install no extensions,
  sign into nothing.
  - `[UNVERIFIED]` `--use-fake-ui-for-media-stream` reportedly auto-accepts the prompt. I did not
    verify it this pass, and it bypasses the permission UI entirely — if it misfires you get no
    microphone at all. The pre-granted profile is the safer route.
- **The mouse cursor is captured** in mirrored output and in any recording. Park it in a corner and
  drive from the keyboard — which §4.3 requires anyway, so it costs nothing.
- **Camera preview mirroring.** `[PRACTICE]` A selfie-mirrored preview (`transform: scaleX(-1)`)
  shows the letter backwards to the room. More dangerous: make sure the frame **sent to the vision
  model** is the un-mirrored one. `[RESEARCH]` Note 07 §2.6 lists, verbatim among Google's own
  best-practice bullets: *"Verify that images are correctly rotated."* Mirrored or rotated text is a
  reliable way to make the read fail.
- Quit Slack, Teams, Discord, Outlook, Steam and OneDrive **entirely**. Do-not-disturb does not stop
  everything.

### 1.4 Windows pre-demo display checklist

`[PRACTICE]` throughout. In order.

| # | Setting | Where | Value |
|---|---|---|---|
| 1 | Mains power | — | Battery saver dims the screen and can throttle |
| 2 | Disconnect any second monitor | — | One output, one surprise fewer |
| 3 | Display mode | `Win`+`P` | **Duplicate**, not Extend. Extend means a dialog can open on the screen you cannot see. |
| 4 | Resolution **after** plugging in the projector | Settings → System → Display | Duplicate forces a common resolution across both, often dropping you to 1920×1080 or 1280×720. **Your viewport changes the moment you plug in.** Rehearse plugged in. |
| 5 | Display scale | Settings → System → Display → Scale | 100%, or whatever you rehearsed at. Never change it on the day. |
| 6 | App mode | Settings → Personalisation → Colours | **Light** (§1.2) |
| 7 | Night light | Settings → System → Display | **Off** — warms the picture, flattens contrast |
| 8 | Adaptive brightness / "optimise content shown" | Settings → System → Display → Brightness | **Off** — it dims dynamically and washes the demo out mid-sentence |
| 9 | Brightness | — | 100% |
| 10 | Do not disturb | Settings → System → Notifications | **On.** Check the automatic rules too — Windows 11 has one for "when duplicating your display". |
| 11 | Screen and sleep | Settings → System → Power & battery | **Never**, on both battery and plugged in |
| 12 | Screensaver, dynamic lock | Lock screen settings | Off |
| 13 | Windows Update | Settings → Windows Update | Pause; no pending restart |
| 14 | Desktop | — | Plain wallpaper, no personal files, taskbar cleared |
| 15 | **Audio output device** | Settings → System → Sound | **Check after plugging in HDMI.** Windows frequently switches default output to the projector, which usually has no usable speakers. The single most common "the demo is silent" cause. |
| 16 | Audio input device | Settings → System → Sound | The headset mic, not the laptop array |

### 1.5 Audio: the risk nobody checks until it fails

`[PRACTICE]` This is a voice demo. `docs/submission.md` Section B already says "external speaker if
the room is bigger than 20 people". Two things it does not cover:

- **Use a close-talking headset mic for the presenter.** A laptop array mic picks up the whole room
  and the agent's own voice.
- **Feedback causes self-interruption, and it looks exactly like a bug.** If the agent's voice comes
  out of a loud PA and back into the laptop mic, voice activity detection can read it as the user
  speaking. `[RESEARCH]` Note 04 §7.1 documents that barge-in is handled automatically client-side
  on the server's `interruption` event, with a stale-audio guard that **drops queued audio so the
  agent cannot resume a cut-off sentence**. In a feedback loop the agent cuts itself off mid-word
  and never recovers the sentence — and it will do it during the window Section B calls "the agent's
  moment" (≈0:58–1:13 in the reworked script), which is the one stretch of the demo you cannot
  afford to lose, and which arrives about eight seconds after the read starts (§0.2).
- **Mitigation: push-to-talk.** `[RESEARCH]` Note 04 §9.3 documents `setMuted(isMuted)` (React) and
  `conversation.setMicMuted(true|false)` (vanilla). Hold `Space` to talk, muted otherwise. This also
  gives you the clean keyboard affordance §4.3 wants — and it makes the scripted barge-in (≈1:13 in the reworked script)
  *deliberate* rather than a race against feedback.

---

## 2. Camera under hackathon lighting

`docs/submission.md` Section B gives the holding technique: both hands, thumbs at the bottom
corners, 30–40 cm, letterhead level with the top of the preview, tilted back ~10°, still for two
seconds. **That is right.** This section explains why, sharpens the distance, and covers what to do
when the room fights you.

### 2.1 The physics, one paragraph each

**Glare.** Specular reflection obeys angle-in = angle-out. A bright source behind or directly above
the camera bounces off a page facing the camera straight into the lens as a blown-out patch, and the
text under it is gone. `[PRACTICE]` Overhead fluorescent panels are large diffuse sources — bad when
the page is **laid flat** and the camera looks down (ceiling reflects straight back), much better
when the page is held **roughly vertical** and tilted so the brightest panel's reflection falls above
or below the lens. This is what Section B's "tilted back about 10°" is buying you.

**Paper.** `[PRACTICE]` Plain matte office paper (80 gsm), as Section B says. Never photo paper,
never gloss, **never a laminate pouch or plastic wallet** — a laminate is a mirror.

**Where the light must be.** `[PRACTICE]` In front of the page, off-axis by 30–45°, ideally two
sources at ±45° or one source plus a white bounce. Never behind the page; never behind the presenter.

**Backlighting.** `[PRACTICE]` A window or — the usual hackathon case — **the projection screen
behind the presenter** destroys auto-exposure: the camera meters the bright field and the page goes
black. Turn the laptop so the camera faces *away* from the screen, or step to the side. Section B
calls backlight "the #1 cause of an unreadable frame" and that matches my read of the physics.

**Free fill light.** `[PRACTICE]` The laptop display at full brightness showing a **light** UI is a
decent soft frontal source at ~40 cm. Another reason for the light theme in §1.2.

**Distance.** `[WEB]` Typical webcam diagonal FOV is around 70–78°, with wide models at 95°
([Microsoft Modern 1080p 78°; Lenovo 510 FHD / Kensington W1050 95°; JLab GO 75°; Targus Webcam Plus
67°](https://www.bhphotovideo.com/c/buy/computer-camera-hd-usb-webcams/ci/6499/pn/5)). `[CALC]` For a
16:9 sensor a 78° diagonal gives ≈43° vertical FOV, and a 297 mm A4 page fills that at **≈ 37 cm**;
70° gives ≈43 cm; a wide 95° gives ≈28 cm.

**Focus — and a refinement to Section B.** `[WEB]` Many laptop webcams are **fixed-focus with a
usable range of roughly 0.4 m to 1.5 m**
([JLab GO USB Webcam](https://www.bhphotovideo.com/c/product/1795578-REG/jlab_wgocamrblk124_go_usb_webcam_black.html)).
That collides with the distances above: on a fixed-focus camera, **30 cm may be inside the near
focus limit**, so the page is softest exactly when it is biggest. **Use the far end of Section B's
30–40 cm range — aim for 38–40 cm, not 30.** Autofocus models instead hunt for 1–2 seconds whenever
the page moves, which is the other half of why Section B says hold still for two full seconds.

**Motion blur and shake.** `[PRACTICE]` A webcam in a dim room drops to long exposures; handheld A4
at 40 cm smears. Blur destroys small text before it destroys anything else. `[RESEARCH]` Note 07
§2.6, verbatim from Google's best-practice bullets: *"Use clear, non-blurry images."*

**Flicker.** `[PRACTICE]` On 50 Hz UK mains, cheap LED and fluorescent lighting flickers at 100 Hz
and produces rolling bands unless exposure is a multiple of 10 ms. Most webcam drivers expose a
"Powerline frequency / anti-flicker" setting — **set it to 50 Hz.** Routinely missed, and it
presents as a mysterious intermittent read failure.

### 2.2 The one physical setup to use

1. Laptop on a table at working height, lid ~100°, **camera facing away from the projection screen
   and away from any window**.
2. Printed letter **mounted on stiff A4 card or a clipboard** so it cannot curl. (Section B's second
   face-down copy guards against creases; card prevents the curl that triggers the skill's
   "flatten it out" branch.)
3. Both hands, thumbs at the bottom corners clear of the date block, **elbows braced on the table**.
4. **38–40 cm from the lens.** Fill ~85% of frame height, not 100% — stays outside a fixed-focus
   near limit, tolerates drift, wastes nothing.
5. Page roughly vertical, tilted back ~10°.
6. **Completely still for two full seconds.** Autofocus needs it; exposure needs it; Section B's
   script already budgets for it.
7. Lock exposure, focus and white balance in the webcam driver if your hardware allows, then never
   touch them.

### 2.3 Fallback if the room is too dark

1. **A second bright window as a lamp** — a blank white full-screen page aimed at the paper, if you
   have a second display.
2. **Phone torch bounced off a sheet of white A4** at 45°. Bounced, never direct: a direct torch is a
   hard specular hotspot and strictly worse than no light.
3. **A clip-on LED panel or small ring light.** £15, weighs nothing, solves it outright. Pack one.
4. **Switch the input from live camera to an uploaded still.** `[PRACTICE]` An "upload a photo
   instead" path is a legitimate product feature — a blind user may well be sent a photo by a sighted
   relative — and it doubles as a demo fallback: upload a known-good, perfectly-lit photo of the same
   letter and continue.

### 2.4 Assessment of the test-letter PNGs on disk

> **⚠️ STALE — `test-letters/` was regenerated while this pass was underway. Re-measure before
> relying on the table below.** `[REPO]` `generate.py` now sets `DPI = 300` and
> `W, H = 2480, 3508`, has a points-to-pixels helper and a bottom-margin overflow check, and the
> three PNGs have been re-rendered (01-hospital-appointment.png is now ~505 KB, up from ~185 KB).
> **That is this section's recommendations being acted on, which is good** — but every figure below
> was measured against the old 150 DPI render and the derived point sizes are no longer right. The
> *method* and the *targets* still stand; the numbers need redoing. Editing `generate.py` was
> explicitly out of scope for this pass, so this is a flag, not a fix.
>
> One knock-on for §3.3G: at ~505 KB the source PNG is now twice the ≤250 KB upload target, and
> `docs/research/08-gemma-live-api-test-results.md` §3's "185 KB PNG / 258 image tokens" figure was
> measured against the *old* file. Client-side downscaling before upload matters more now, not less.

`[REPO]` Measured from `test-letters/generate.py` and the three rendered PNGs **as they were at
commit `39b8655`**. The canvas was `W, H = 1240, 1754` — exactly A4 at 150 DPI — so point size =
pixel size × 0.48.

| Element | Source px | Point size at A4 | Contrast on white `[CALC]` |
|---|---|---|---|
| Letterhead org name | 46 bold | **22.1 pt** | 9.0:1 blue `#0a468c`, 9.2:1 red `#8c141e`, 7.4:1 green `#145f46` |
| Strapline | 23 | **11.0 pt** | **6.2:1** (grey `#5f5f5f`) |
| Section headings | 28–34 bold | 13.4–16.3 pt | 17:1 (`#1a1a1a`) |
| Body text | 27 | **13.0 pt** | 17:1 |
| Reduced body (letter 02) | 24 | **11.5 pt** | 17:1 |
| Key-value box — **label** | 24 | **11.5 pt** | **6.3:1** (grey `#5a5a5a` on panel `#f6f5f1`) |
| Key-value box — **value** | 28 bold | 13.4 pt | 17:1 |
| Consent-slip lines (letter 03) | 24 | **11.5 pt** | 17:1 |
| Margins | 110 px | **18.6 mm** left/right | — |

**The contrast is fine. The size is not.** Working it through the capture chain:

`[CALC]` A4 filling 85% of frame height maps the 1754 px source to 612 px at 720p (scale 0.35) or
918 px at 1080p (scale 0.52). The 27 px body glyph therefore lands at **9.4 px em (~4.9 px x-height)
at 720p** and **14.1 px em (~7.3 px x-height) at 1080p**. `[PRACTICE]` The conventional comfort floor
for reliable text extraction is around 20 px cap height / 10 px x-height — the same reason OCR
guidance asks for ~300 DPI scans of 10 pt text. **Both are below it; 720p is badly below it.**

`[RESEARCH]` Note 07 §2.6 gives the model-side half of the same story, verbatim: *"258 tokens if both
dimensions <= 384 pixels. Larger images are tiled into 768x768 pixel tiles, each costing 258
tokens."* and, on `media_resolution`: *"Higher resolutions improve the model's ability to read fine
text or identify small details, but increase token usage and latency."* Note 07 concludes that for
LetterLens **this is the knob to raise** (the exact enum values are flagged UNCONFIRMED there).
So the levers are: bigger type on the paper, more pixels on the page in frame, and a higher
`mediaResolution` — traded against latency, which §3 then has to absorb.

`[RESEARCH]` **That trade has got much better since note 07 was written, and it changes the ranking
again.** Note 08 §10 measured the same full-page scans at **258 image tokens** and **3.7–4.5 s** on
the pinned `gemma-4-26b-a4b-it`, with `thinkingLevel: "minimal"` holding on the vision path — zero
thought characters on all three calls. Two things follow. First, image tokens are cheap, so there is
no token argument against sending a legible frame. Second, the backend bounds the call at 60 s
rather than at `LLM_TIMEOUT_MS` (§0.1), so there is no hard gate to breach — but the end-to-end read
is already ~8 s with a tail to 30.5 s (§0.2), and that is the budget `mediaResolution` would spend
against. **Fix it on the paper and in the frame first, where it is free; treat `mediaResolution` as
the next lever and measure the latency cost before relying on it.**

Recommendations:

- **Reprint larger. Do not bother raising contrast** — it is already 17:1 where it matters.
- **Point sizes for an A4 demo print:** body **16–18 pt**, key-box values **20–22 pt**, the headline
  deadline line **24 pt bold**, letterhead 28–32 pt. That puts body x-height at ~9–10 px at 1080p —
  at the floor rather than well under it.
- **Fix the two grey tones.** Box labels at 6.3:1 and the strapline at 6.2:1 are the lowest-contrast
  ink on the page and the first to dissolve under a webcam in poor light. Make the box labels full
  `#1a1a1a`. They are the words "Date", "Time", "Pay reduced amount by" — exactly the semantics
  `read_document` must land, and exactly what feeds its `WHEN:` and `DEADLINE:` lines. (`[REPO]`
  Note that the nine-field structured object in `skills/letter-reader/references/output-schema.md`
  is **not what the backend returns** — it returns six plain `FROM:`/`ABOUT:`/`WHEN:`/`DEADLINE:`/
  `REF:`/`CONTACT:` lines. The schema file is aspirational; see §0.)
- **Print at 300 DPI, not 150.** Either regenerate at `W, H = 2480, 3508` with all sizes doubled, or
  typeset the `.txt` files in a word processor at the sizes above and print from there.
- **Reclaim the right margin.** `[REPO]` `generate.py` wraps body text at `wrap=62` characters, so the
  ink column uses only ~60–70% of the page width and the right third of every letter is blank.
  Widening the measure means 18 pt fits in the vertical space 13 pt occupies now.
- **`[REPO]` Watch the page overflow.** `generate.py` draws top-to-bottom with a running `self.y`
  cursor and **has no bottom-margin or overflow check**. All three letters already end within a few
  millimetres of the 1754 px bottom edge — letter 03's "Signed: ___ Date: ___" is the last thing on
  the page with essentially no margin. Enlarging the type will silently push content off the bottom.
  Add an assertion, or split to two pages.
- **Make a trimmed "demo print" variant.** `[PRACTICE]` Keep the full letters for realism; print a
  one-page demo variant containing only sender, title, key-value box and deadline at 18 pt+. It reads
  reliably and fills the frame — and per `skills/letter-reader/SKILL.md` the spoken answer is capped
  at 40 words anyway, so the parking-shuttle paragraph was never going to be said out loud.

*(All recommendations. I have not modified `generate.py` or regenerated any PNG. **Note that
somebody else has**, concurrently with this pass — see the staleness warning at the top of §2.4.
Several of the recommendations above, including the 300 DPI render and the overflow assertion,
appear to be done already. Re-measure rather than assuming either way.)*

---

## 3. Wi-Fi dies mid-demo

Five distinct failure points with five different signatures. `docs/submission.md` Section B gives
the one-liner to say; this is what is actually happening and what to do about it.

> **⚠️ The premise of this section changed three times. Here is where it landed.** The scary figures
> came from `gemma-4-31b-it` and are gone. But the model-call figure (3.7–4.5 s) is not the wait
> either. Per §0.2 a **healthy end-to-end read is ~8 seconds**, with a measured tail to **30.5 s**,
> so **ten seconds of dead air is normal and the abandon time is 35 s.** §3.1a earns its place more
> than ever: the discriminators are how you confirm what broke without touching the laptop.
>
> **⚠️ And the failure *inventory* changed, which matters more.** This section was written for a
> tunnelled webhook architecture. **There is no tunnel** (see the front matter): `read_document` is a
> client tool, the browser calls `http://127.0.0.1:8000` directly, and ElevenLabs' cloud never
> reaches the laptop. Failure modes 1 and 4's tunnel content is **dead**. The live failure modes on
> the real architecture are: **camera/mic permission, CORS, the backend process being down, a 429
> from the free tier, and a slow-but-healthy read.** The network still matters — the ElevenLabs
> session and the Gemini API both need it — but there is no tunnel URL to go stale.

### 3.1 The failure table

| # | What breaks | What the audience sees/hears | Presenter's next 5 seconds |
|---|---|---|---|
| 0 | **Nothing. The read is just in flight.** | Up to ten seconds of silence after the agent says "let me read that for you". | **Keep narrating through your block.** A read is ~8 s and the tail reaches 30.5 s (§0.2); if you are still talking at fifteen seconds, start working the §3.1a discriminators. Do not touch anything, do not reach for the keyboard, do not say "hmm". |
| 1 | **The backend process is down, or the browser cannot reach it** — backend not started, crashed, wrong port, or the page origin is not in `CORS_ORIGINS` | Greeting fine, then after you hold the letter up: the tool returns an error almost **instantly** — too fast to be a model call — and then either silence or, worse, a confident summary of a letter it never read. See 3.2. | **The speed is the tell: a failure inside two seconds is not the model.** Stop it talking. *"That's our local backend, not the model."* Go to the recording. Do not debug on stage. |
| 2 | **ElevenLabs session drops mid-sentence** | The agent **cuts off mid-word**. Silence. | *"We just lost the voice session — this is live over conference wifi."* One reconnect attempt, ~5 s. Then the recording. |
| 3 | **Vision call fails or times out** (the backend bounds it at 60 s, not at `LLM_TIMEOUT_MS` — §0.1) | A long gap, then the agent says it could not read the letter and gives one physical instruction. | Section B's line still covers this and it is still the right one. Use the **second printed copy**, flatter, closer. **One** retry — and budget another ~8 s for it. |
| 4 | **Congested wifi / captive-portal re-auth** | Everything *looks* connected. Nothing responds. Long pauses everywhere — **including on the conversational turns, which is the tell** (§3.1a). | *"Conference wifi. Switching to my hotspot."* Switch (pre-tested — 3.3C). **Good news: the switch costs you nothing structural** — the backend is on localhost, so there is no URL to re-register. The browser's mic and camera grants also survive, because the origin never changes. |
| 4a | **429 from the Gemini free tier** | One read fails or stalls noticeably longer than the others; the backend terminal shows the 429 and a retry. | Nothing to say — let the retry run, add ~8 s to your estimate. The free tier is 30 RPM; the backend must **honour `RetryInfo.retryDelay` as a floor** (§0.2), and one 429 advertised 17 s while real recovery took 22.8 s. If you have burned a lot of calls rehearsing, this is the likeliest single failure on the day. |
| 4b | **Camera or microphone permission not granted** | No preview, or the session never starts; possibly a browser dialog on the projector. | *"New profile, fresh permission."* Accept it. §1.3's persistent profile and the T-10 check exist to make this impossible. |
| 5 | **The model's scratchpad reaches the agent** (§0.3) | The agent starts speaking and does not stop — rambling, self-correcting, nothing like a letter summary. | Interrupt it. *"That's the model's scratchpad leaking through — one for the backlog."* **No retry will fix this**; the bug is in the backend. Go to the recording. |

Failure #3 is still the one to relax about, and the *behaviour* is good:
`skills/letter-reader/SKILL.md` has a whole **"When the image is unusable"** branch that picks one
concrete physical instruction — closer, flatten, tilt, turn, steady — and caps retries at three
before suggesting a trusted person. That is designed behaviour, and Section B is right that you
should sell it rather than apologise for it. The *arithmetic* is the part to watch: at ~8 s end to
end (§0.2), the skill's three-retry cap is **~24 seconds** and on the tail it is worse, so the cap is
affordable in the product and **not** affordable on stage. **Take one retry and move on** — on a
model that went 19/19 (§0.2), a second failure is a signal about your setup rather than bad luck, and
no third attempt will fix it.

### 3.1a Telling a slow read from a dead one — the discriminators

This is the skill demo day still demands of you, and it is a real one: an **eight-second** silence is
the healthy case and the tail runs to **30.5 s** (§0.2), so the question is not "is it slow" but "is
it alive". You need to know, without stopping and without touching the laptop, whether to keep
talking or to cut.

**Set an abandon time before you stand up. Use 35 seconds** — past the 30.5 s worst case
`backend/app.py` actually recorded, and inside the backend's own 60 s bound so you are not waiting on
a call that has already been given up on. Earlier drafts said 75 s (that was `gemma-4-31b-it`) and
then 15 s (that was the raw model-call figure mistaken for the wait). **15 s would abandon reads that
were going to land.** Start counting from the moment the agent says *"let me read that for you"*, not
from when you raised the letter. **Below 35 s you narrate. At 35 s you stop and run the recovery
line, regardless of what you believe is happening.** The value of a pre-committed number is that it
removes the decision from the worst possible moment to be making one.

**Thirty-five seconds is a long time to fill, so plan the fill.** This is the one place the old
"narrate over a long pause" structuring advice is still useful — not because the model is slow, but
because the tail is real. Have two stoppable narration blocks ready, not one.

What to look at while you wait, in order of how much it tells you:

| Signal | Healthy slow read | Something is actually broken |
|---|---|---|
| **How fast it failed, if it failed** | n/a | **A failure inside two seconds is not the model — it is the local backend or CORS.** The model cannot answer that fast. This is the cheapest discriminator in the table and it needs no action from you at all. |
| **The agent's spoken "let me read that for you" at the start** | **Played.** The tool call reached the agent and the agent acted on it. | **Never played.** The agent never started the tool call — that is a session or config problem, not a slow model. Do not wait out the 35 s; you are waiting for nothing. |
| **The on-screen `Reading your letter…` state** | Up and stays up. | Never appeared, or it appeared and then cleared with no spoken result — the latter means the tool returned and something downstream ate the answer. |
| **Ask the agent a throwaway question** — *"and while that's going, can you still hear me?"* | **It answers, fast — about two seconds.** The conversational path is the same `gemma-4-26b-a4b-it` and the same quota bucket as the read (§0.2), so a fast answer tells you the session and the model are both healthy and whatever is wrong is in the `read_document` path or the frame. **This is still the single best discriminator you have.** | **Silence.** The session or the network is gone, not the model. Stop waiting and go to recovery. |
| **Backend terminal** (`Alt`+`Tab` 2, §5.1) | The inbound `POST /read_document` is logged and one Gemma request is in flight, waiting. | **No inbound request logged at all** — the process is down or on the wrong port. **An `OPTIONS` preflight logged but no `POST`** — that is CORS: the origin is not in `CORS_ORIGINS` (§1.3). Or: a 429 and a retry in progress (fine, but add ~8 s), or a traceback (go to recovery). |

**Use the fourth row.** It is the only one that works from where you are standing, it costs five
seconds, it sounds completely natural to the room, and it cleanly separates "the slow thing is slow"
from "everything is dead". Build it into the script as a line you *may* use, so it does not sound
improvised when you do.

**Do not** reach for the keyboard, refresh, or peer at a terminal while the room watches. Every one
of those reads as panic, and four times out of five you would have been interrupting a healthy read.

### 3.2 Failure #1 deserves its own warning — the agent inventing a letter it never read

`[RESEARCH]` Note 03 records this verbatim from the ElevenLabs API reference:

> `tool_error_handling_mode` (enum, optional, default: `auto`) — "Controls how tool errors are
> processed before being shared with the agent. 'auto' determines handling based on tool type
> (summarized for native integrations, **hide** for others) …"

and concludes:

> **So with the default `auto`, a custom webhook tool's error is HIDDEN from the agent.** … Set it
> to `"summarized"` explicitly or the agent will narrate success after a failed save.

`[RESEARCH]` Note 03's **independent adversarial verification pass** (added in commit `39b8655`)
re-fetched every source and lists claim 14 as **CONFIRMED**, annotated "Verbatim — the build's
biggest footgun". This is not a soft claim.

`[UNVERIFIED]` **One qualification, since the architecture changed.** Note 03 read that enum in a
*webhook* context, and `read_document` is now a **client** tool. The enum text says `auto` hides
errors for everything that is not a "native integration", and a client tool is not one — so the
footgun almost certainly still applies — but nobody has confirmed the client-tool case against a
doc page or a live session. Treat it as live until someone does.

`[REPO]` **And `agent/tools/read_document.json` does not set `tool_error_handling_mode` at all**, so
it is on `auto`. That is the one field the file is missing.

For LetterLens: **if `read_document` fails, the agent may not be told, and will invent a letter
summary** — in a demo of an assistive product for blind people, in front of judges, about a date
someone would act on. It is the exact failure
`skills/letter-reader/SKILL.md` spends three sections forbidding, arriving through a channel the
skill cannot see.

**Set `tool_error_handling_mode: "summarized"` on `read_document` before demo day** — it is the one
tool there is (§0). It is already on the `docs/submission.md` Section D checklist. Tick it.

`[RESEARCH]` Reinforce it in the prompt too. Note 03 flags: *"What the agent literally says on
timeout/failure: UNCONFIRMED. No doc page states a canned phrase."* `agent/persona-prompt.md`'s
operating rules say the right thing in prose but **the system prompt text itself does not** — which
`docs/submission.md` also flags as recommendation 4. The prompt cannot act on an error it never
receives, and it cannot follow a rule that lives only in a Markdown heading above it.

### 3.3 Mitigations, ranked, with a hard line between "before" and "on the day"

#### MUST be prepared before demo day — cannot be improvised

**A. ~~A reserved tunnel hostname.~~ RETIRED — there is no tunnel.** `[REPO]` `read_document` is a
**client** tool (`agent/tools/read_document.json`, `"type": "client"`), so the browser calls
`http://127.0.0.1:8000` itself and ElevenLabs' cloud never has to reach this laptop. There is no
`api_schema.url` to go stale, no `PUBLIC_BASE_URL`, no `TOOL_WEBHOOK_SECRET`, and nothing to start
before the demo except the backend and the dev server.

**Say this out loud if a judge asks about reliability**, because it is a genuine engineering win and
not just an absence of work: a tunnel is a dependency that dies quietly in the middle of a demo and
takes 2–5 minutes to re-register. Making the tool client-side deleted that failure mode outright
rather than mitigating it. The analysis this item used to contain (random subdomains per restart,
`api_schema.url` required server-side) was correct for a webhook architecture and is kept in the
research notes; it no longer applies here.

**B. A pre-recorded screen capture of a successful end-to-end run.** `[PRACTICE]` With audio, shot on
this laptop at the projector's resolution, **stored as a local file** (not YouTube — you will have no
network), open in VLC, paused at frame 0, one `Alt`+`Tab` away. The only mitigation that works when
the network is simply gone, and the only way to deliver Section B's "total collapse" line with
something to show. `docs/submission.md` Section D already wants a demo video for the submission form
— **record it so it doubles as this.** You cannot record a successful run during a failed demo.

**C. A phone hotspot, tested end-to-end.** `[PRACTICE]` Not "I have a hotspot" — SSID saved, laptop
joined at least once, data allowance confirmed, and **the full chain exercised over it**: backend up,
agent connects, `read_document` round-trips. First-time joining on stage costs 60–90 seconds.
**The switch itself is now cheap**: the backend is on localhost and the page origin never changes, so
there is no URL to re-register and the browser's mic and camera grants survive the network change
intact. Only the ElevenLabs session and the Gemini API care that the network moved.

**D. ✅ The model pin, verified with a real 200 *through the backend*. DONE.** See §0.1. `POST
/read_document` returned 200 on the first attempt for all three letters in **8.1 s, 7.6 s and
8.7 s**, verbatim-correct. Re-run it at T-60 on the venue network anyway — that is where the number
changes.

**D2. ~~The split model paths, actually implemented.~~ RETIRED — do not build it.** §0.2. Note 08 §10
settled one model for both paths: 2.0 s median on text, 3.7–4.5 s on vision. `CHAT_MODEL` and
`VISION_TIMEOUT_MS` stay commented out in `.env.example`. The diagnostic this item used to
underwrite — asking the agent a throwaway question mid-read — still works; see §3.1a for what it now
tells you.

**D3. ✅ `thought: true` filtering in the backend. DONE.** §0.3. `[REPO]` `backend/app.py`'s
`_extract_text()` joins only the parts without a `thought` flag, and the vision call runs at
`thinkingLevel: "minimal"` as a first layer. This was three lines of Python standing between you and
the agent reading four thousand characters of model deliberation aloud to the room, and they are
written. Still confirm at T-60 that the spoken result is short — a regression here is silent until
it is on a PA.

#### Cheap, and still before demo day

**E. `tool_error_handling_mode: "summarized"` on `read_document`.** §3.2. Minutes of work. Prevents
the worst outcome. `[REPO]` **Not set in `agent/tools/read_document.json` yet** — it is the only
field missing from that file.

**F. Cover the latency with speech.** `[RESEARCH]` Note 03 §1.3, verbatim: `pre_tool_speech` —
"'auto' (default) decides based on recent tool latency, **'force' always asks the agent to speak**,
'off' fully opts out". ✅ `[REPO]` **Already set to `"force"` on `read_document`**, along with
`tool_call_sound_behavior: "always"` and `interruption_mode: "allow"`. `[RESEARCH]` Also available:
`tool_call_sound` (`typing`, `elevator1`–`4`), and note 04 §7.2's
`conversation_config.turn.soft_timeout_config` with a `message` field — "Message to show when the
first soft timeout is reached while waiting for LLM response." Section B's script hangs its entire
timing on the agent saying *"let me read that for you, one moment"* at ≈0:14; `pre_tool_speech:
"force"` is what makes that line actually happen.

**It is a polish item with an accessibility floor under it, and at ~8 s it is more than polish.** The
pause it covers is **~8 seconds** end to end (§0.2), with a tail to 30.5 s — not the twenty to sixty
we briefly budgeted for on `gemma-4-31b-it`, but not four seconds either. Eight seconds of silence
tells a sighted user "it's thinking" and a blind user nothing, and §3.1a's "did the line play?"
discriminator only exists if the line plays. `soft_timeout_config.message` is **worth configuring**
after all: an eight-second wait with a thirty-second tail is exactly the case a mid-wait reassurance
is for.

**G. Get the timeouts and the frame payload right.** This one has changed substantially, three times.

`[REPO]` `.env.example` still sets `LLM_TIMEOUT_MS=8000`, **and `backend/app.py` never reads it.
That is correct, not an oversight** — a healthy end-to-end read is 8.1–8.7 s, so an 8-second gate
would kill good reads. The vision call is bounded by the backend's own
`httpx.Timeout(60.0, connect=10.0)`. **Do not wire `LLM_TIMEOUT_MS` into the vision path.** Note that
`backend/app.py`'s comments also record a 30.5 s call outliving a nominal 25 s bound, which is why
the 60 s figure is what it is.

`[REPO]` **The tool-side timeout is `response_timeout_secs: 120` in
`agent/tools/read_document.json`, not the 20 s default.** Earlier drafts of this file argued for the
20 s default on the strength of a 3.7–4.5 s model call; that was the wrong comparison. Against a
measured ~8 s read with a 30.5 s tail and a 60 s backend bound, the ordering that has to hold is:

```
backend httpx timeout (60 s)  <  read_document response_timeout_secs (120 s)
```

so the backend fails first and you control the failure message. **Leave `response_timeout_secs` at
120.** `[RESEARCH]` Note 03 §7.1 gives the default as 20 s (range 5–300), re-confirmed in the
verification pass as claim 13 — 120 is inside that range. The ≥120 s figure in the *earliest* drafts
came from `gemma-4-31b-it`'s 36.8–56.8 s vision calls and was arrived at for the wrong reason; it
happens to be the right value for the right reason now. Check what `docs/submission.md` Section D
says and make the two agree.

`[CALC]` + `[REPO]` **Payload size is a measured term, not a projection, and it is the gap between
3.7–4.5 s and 8 s.** The PNGs in `test-letters/` are ~0.5 MB at 300 DPI; base64 inflates that by ~4/3
(`[RESEARCH]` note 07 §2.4), and encoding plus upload is what accounts for roughly half of the
measured end-to-end time even on a good local network. On a saturated conference uplink of ~2 Mbps a
1.5 MB frame would add **~6 seconds** on top. **Client-side downscaling is the single biggest latency
win left on the read path**, and it is the one that would move the ~8 s figure. Downscale and
JPEG-compress
client-side: long edge ~1280 px, quality ~80, **target ≤ 250 KB**, keep it in colour (letterhead
colour is real signal). `[RESEARCH]` Note 08 §3 confirms `inline_data` base64 works in a single
round trip, so there is no Files API hop to budget for. Balance this against the `mediaResolution`
point in §2.4 — you want fewer bytes but not fewer *legible* pixels, which is exactly why §2.4 says
fix it on the paper instead.

**H. Validate the chain at T-10 — but do not expect it to make the model faster.** `[PRACTICE]` At
T-10, on the venue network, with the actual printed letter, run one complete `read_document` round
trip. It validates the whole chain — camera permission, the browser reaching `127.0.0.1:8000`, CORS,
the signed-url mint, agent config, the vision call, thought-part filtering, audio out — at the last
possible moment, and it gives you one real latency sample for tonight's network.

`[RESEARCH]` **It will not warm anything.** Note 08 §1.2 raised the "latency is thinking tokens"
hypothesis and then killed it — a `thinkingLevel: "minimal"` probe with zero thought characters still
took 36.2 s on `gemma-4-31b-it`, so the model was the whole variable. **But do two runs, not one**,
because the thing you are sampling has a tail (5.1, 5.5, 8.2, 14.4, 30.5 s — §0.2) and one sample
tells you nothing about it. The constraint on doing more is the free tier's 30 RPM and a 429 being
the likeliest single failure (note 08 §6: *"never conclude a capability is unsupported from 5xx
alone"*).

**I. A canned/mock path.** `[RESEARCH]` Two documented routes:
- **Client-side**, note 04 §3: a session option
  `toolMockConfig?: { mockingStrategy?: "none" | "all" | "selected"; mockedToolNames?: string[]; fallbackStrategy?: "raise_error" | "call_real_tool" }`.
  A `?mock=1` flag setting `mockingStrategy: "selected", mockedToolNames: ["read_document"]` is
  perhaps thirty minutes of work.
- **Server-side**, note 03 §8: `response_mocks` on the tool, with a required `mock_result` string and
  optional `parameter_conditions` — "Evaluated top-to-bottom; first match wins."

**Be clear-eyed about what this buys.** It removes the vision hop and the backend. It does **not**
remove the ElevenLabs session, which still needs the network. It covers "the vision call is slow or
down". It does not cover "the wifi is dead". For that, only B works.

**It has, however, been demoted.** At ~8 s and 19/19 with no 5xx (§0.2), the mock is a break-glass
option for a dead network rather than a timing strategy — `docs/submission.md` Section B no longer
needs option C, and a 90-second script can be run live. ~~The 30-second cut-down~~ is the one case
where it would still earn its place: ~8 s of a 30-second slot is a quarter of the slot. **The
condition is disclosure:** one spoken sentence — *"the vision call is stubbed here so I fit the slot;
come to the table and I'll run it live"* — and it is completely fine. Undisclosed, in a public repo,
in front of judges, it is not. If you build the flag, build the sentence into the card next to it.

**J. There is no cheap true-offline LetterLens.** The voice agent is a hosted service. Do not spend
demo week building local TTS; spend twenty minutes recording B.

#### On the day only

- **Ethernet if the venue has a port.** Pack a USB-C → RJ45 dongle. A wired link beats everything above.
- **5 GHz / 6 GHz only.** 2.4 GHz at a hackathon is unusable. Forget the 2.4 GHz SSID so Windows
  cannot drift onto it.
- **`[RESEARCH]` If the venue blocks UDP**, note 04 §10 documents `webRtc.iceTransportPolicy`,
  verbatim: 'Set to "relay" to only use TURN relay candidates, e.g. on networks that drop direct UDP
  flows. Defaults to "all".' Expose it behind a flag and **test at T-60** — you cannot diagnose a UDP
  block from the stage.
- **Captive-portal re-auth.** Many venue networks silently drop you after an hour. If everything
  stops at once with no error, re-open the portal page before touching anything else.

### 3.4 Two architecture decisions that already protect you

**1. Everything is localhost.** `[REPO]` `.env.example` sets
`CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`, the frontend is served from localhost,
and the backend is reached at `http://127.0.0.1:8000` **by the browser, not by ElevenLabs' cloud**.
Nothing is tunnelled and nothing is deployed. Keep it that way.
`[RESEARCH]` Note 04 §9.2 records that `navigator.mediaDevices` needs a secure context — HTTPS or a
localhost-family origin — so `http://localhost:5173` is fine where a LAN IP would not be. More
importantly for §3: **browser permissions are per-origin, and this origin never changes.** A
tunnelled UI would get a new origin on every tunnel restart and lose the granted microphone
permission, producing a permission dialog live on stage on top of whatever else was going wrong.
Localhost makes the mic and camera grants survive every network event, including a hotspot switch.

**The cost of this is one new failure mode, and it is the one to check at T-60:** the page origin
must be in `CORS_ORIGINS`. `vite preview` serves on **4173**, not 5173 (§1.3), so presenting from a
preview build with the stock `CORS_ORIGINS` is a silent CORS failure that looks exactly like a dead
backend. The §3.1a discriminator for it is an `OPTIONS` in the backend log with no `POST` after it.

**2. `ELEVENLABS_API_KEY` never reaches the browser.** `[REPO]` `GET /signed-url` mints a
short-lived ElevenLabs conversation token server-side and the frontend fetches that instead of
holding a key. Verified live: HTTP 200 in 1.4 s with a real token. This is the one thing that still
*has* to be server-side, and it is the reason the backend exists at all beyond the vision call.

---

## 4. Accessibility of the demo itself

LetterLens is for blind and low-vision people, and `skills/letter-reader/SKILL.md` holds the *agent's
speech* to a genuinely high standard — no "as shown above", no "the table below", most important
fact first. **The UI currently has no equivalent.** Judges will notice the gap, and they should.

Each item is a requirement plus the one-line reason. **None of this is CSS I am writing** — these are
requirements for whoever owns the styling and the components.

### 4.1 The double-speak trap — read this one first

**Requirement: the agent's spoken words must NOT be inside an `aria-live` region.**

If the transcript of what ElevenLabs is speaking is announced by a live region, a screen-reader user
hears every sentence **twice**, overlapping — once from the TTS, once from NVDA / JAWS / VoiceOver.
Live-region announcements queue against the screen reader's own speech, not against your audio
stream, so they cannot be made to stay in sync.

1. **Render the agent transcript in a plain, non-live container.** Note that `role="log"` carries an
   *implicit* `aria-live="polite"` — using it is the same mistake wearing a hat. Use a labelled
   region (`<section aria-label="Conversation transcript">`) with no live semantics.
2. **Reserve `aria-live="polite"` strictly for state the agent does not say aloud:** "Camera ready",
   "Reading your letter…", "Microphone muted", "Connection lost". (The fourth example this list used
   to give, "Calendar file downloaded", is gone: `add_event` is **NOT BUILT** — see §0.)
3. **Offer it as a user setting, defaulting off.** A deaf-blind judge on a braille display gets
   *nothing* from the TTS — braille is driven by the screen reader, so for them the live region is
   the only channel. One toggle, off by default, is the correct answer.

**Never use `aria-live="assertive"` for anything the agent also speaks** — assertive interrupts the
screen reader mid-sentence. Reserve it for errors, and prefer polite even there.

### 4.2 Structure and screen-reader expectations

| Requirement | Why |
|---|---|
| Real landmarks — `<header>`, `<main>`, `<footer>`, one `<h1>`, headings in order | Screen-reader users navigate by landmark and heading, not by scrolling. A `<div>` soup means a blind user cannot find the transcript at all. WCAG 1.3.1, 2.4.1 |
| `[REPO]` Change `<title>frontend</title>` to "LetterLens" | First thing a screen reader announces, and `docs/submission.md` already flags it as on-screen during the demo |
| `[REPO]` `<html lang="en">` is already correct — keep it | Drives screen-reader pronunciation |
| The camera `<video>` gets `aria-hidden="true"`, with a **text** status beside it | A live video feed conveys nothing to a blind user. Give them "Letter detected — hold still" as text, not an alt-text essay. |
| Every error the agent speaks also appears on screen, and vice versa | WCAG 3.3.1, and it is how the room follows a failure. The skill's retry instructions ("hold it a bit closer") should be visible as well as spoken. |

### 4.3 Keyboard, focus, and starting the mic

| Requirement | Why |
|---|---|
| **Everything operable by keyboard** — native `<button>`/`<a>`, tab order matching reading order, no `<div onClick>`, no keyboard trap | WCAG 2.1.1 / 2.1.2. You are driving from the keyboard anyway to keep the cursor off the projector (§1.3). |
| **The mic must be startable without a mouse** — one documented key, e.g. `Space` to start/stop, `Escape` to end | A blind user cannot find a button with a mouse. Browsers require a user gesture for `getUserMedia` and audio playback, **and a keypress is a valid gesture** — a global `keydown` handler satisfies the policy. Do not auto-start on load; it will be blocked and it is hostile. |
| Say the key binding **in the agent's first message** and show it on screen | `[REPO]` The current first message — "Hold a letter up to the camera and I'll tell you what it says" — never says how to begin. |
| `[RESEARCH]` Call `navigator.mediaDevices.getUserMedia({ audio: true })` yourself, from that gesture, **before** `startSession` | Note 04 §9.1, verbatim from the ElevenLabs docs: "Consider explaining and allowing microphone access in your app's UI before starting the conversation." §3.4 gives the reason it matters in React: `startSession` **does not reject** on failure, so without the pre-flight "denied mic" and "connection failed" are indistinguishable. |
| **Visible focus indicator, ≥3 px / 0.4 vh, ≥3:1 against both the component and its background** | WCAG 1.4.11, 2.4.7 (2.2 adds 2.4.11 Focus Not Obscured and 2.4.13 Focus Appearance). A 1 px default outline is invisible on a projector — this is a legibility requirement too. Do not `outline: none`. |
| **Do not steal focus mid-utterance.** Give a new result card `tabindex="-1"` and move focus only on explicit user action, or announce "Result ready — press R" | Moving focus interrupts the screen reader and loses the user's place. WCAG 2.4.3, 3.2.1. |
| ~~After the `.ics` download from `add_event`, announce the filename and location~~ **NOT BUILT — no requirement to meet.** `add_event` and the `.ics` download do not exist (§0). Keep the reasoning for whenever a download does ship: a browser download is a focus and announcement black hole, so it belongs in the polite live region, where the agent does not speak and there is no conflict. | — |

### 4.4 Captions

**Requirement: render the agent's speech as large on-screen text, live, with scrollback.**

`[RESEARCH]` The source already exists: note 04 §6.4 documents the `onMessage` payload as
`{ message, event_id, role: "user" | "agent", … }`, with agent and user turns both routed through
`onMessage`. `WordTimestamp` / `onAudioAlignment` are exported if you want word-level timing later.

Three reasons at once:
- Deaf and hard-of-hearing judges can follow a voice demo only through captions.
- A hackathon room is loud; captions are often the only way *anyone* follows it.
- It is the same element as the 6.5 vh caption line in §1.1 — one component serves the deaf judge
  and the back row.

`[RESEARCH]` **Check the box or it silently does not work.** Note 04 §6.6 warns some client events
must be explicitly enabled in the agent's Advanced → Client Events tab, naming
`agent_chat_response_part` as one that is off by default in voice conversations and "silently breaks
a feature". `docs/submission.md` Section D already has the equivalent line for `interruption` —
**add `agent_chat_response_part` to that checklist**, or your captions will simply not appear.

### 4.5 Motion, colour, and timing

| Requirement | Why |
|---|---|
| **`prefers-reduced-motion: reduce`** flattens the listening orb, waveform, spinners and card transitions to a static state | Vestibular disorders. WCAG 2.3.3; 2.2.2 for anything auto-updating. The `getInputByteFrequencyData()` visualiser is a continuous animation and needs a static alternative. |
| Nothing flashes faster than 3 Hz | WCAG 2.3.1. A fast-pulsing "listening" dot is the usual offender. |
| **Never state anything by colour alone.** The status pill reads the words "Listening" / "Speaking" / "Reading your letter" / "Disconnected" — not just a green or red dot | WCAG 1.4.1. ~8% of men have a colour-vision deficiency, **and a washed-out projector destroys hue discrimination anyway** (§1.2), so this is simultaneously a projector fix. |
| Text resizes to 200% without loss; reflows at 320 CSS px | WCAG 1.4.4 / 1.4.10. Directly relevant because you may hit `Ctrl` `+` on stage. |
| No information available only on hover | WCAG 1.4.13 — and nobody can see your hover on a projector. |
| **`[RESEARCH]` Set `turn_eagerness: "patient"` and a generous `turn_timeout`** | Note 04 §7.2: `turn_timeout` is seconds, range 1–30, and the docs warn shorter timeouts "may interrupt users who need more time to respond". A low-vision user fumbling a sheet of paper **is** slow. An assistive product that talks over a hesitant user fails its own brief. |
| **The agent must narrate its own waiting — the wait is ~8 seconds, with a tail to 30.5 s** | §0.2. Eight seconds of silence tells a sighted user "it's thinking" and a blind user nothing, and they have no screen to check. ✅ `pre_tool_speech: "force"` is already set on `read_document` (§3.3F). At this length `soft_timeout_config.message` **is** worth adding as a mid-wait reassurance. Keep the on-screen `Reading your letter…` state in the polite live region (§4.1) — it is state the agent does not speak, so there is no double-speak conflict. |
| **Never let the agent speak the model's reasoning** | §0.3. If `thought: true` parts are not filtered, the agent reads 4,236 characters of deliberation aloud. For a sighted user that is embarrassing; for a blind user it is actively harmful — there is no visual cue that what they are hearing is not their letter, and the spoken content contains plausible-sounding wrong answers the model is in the middle of discarding. This is the single worst accessibility failure the build can ship. |

### 4.6 What to actually test, and how

`[PRACTICE]` Thirty minutes, the day before:

1. **Unplug the mouse.** Run the whole demo keyboard-only. If you cannot, neither can a judge.
2. **Turn on NVDA** (free, Windows) and run it again with the monitor off. The §4.1 double-speak is
   instantly audible if it is there.
3. **Zoom to 200%** and check nothing is clipped or unreachable.
4. **Set Windows to "Reduce motion"** (Settings → Accessibility → Visual effects); confirm animations stop.
5. **Photograph the screen with your phone and look at it in bright light.** A crude but startlingly
   good proxy for a washed-out projector.

---

## 5. One-page demo-day runbook

Use with `docs/submission.md` Section B, which has the script itself and its own pre-stand-up
checklist. This one is timed and goes wider.

### T-60 minutes — at the venue, on the venue network

**Start the two processes first; everything else checks them.**

- [ ] **Backend up:** `python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`. Leave the
      terminal visible — it is a §3.1a discriminator.
- [ ] **`GET /health` reports both keys loaded.** `curl http://127.0.0.1:8000/health` and read it:
      `gemini_key` and `elevenlabs_key` must both be `true`, and `vision_model` must say
      `gemma-4-26b-a4b-it`. **There is no tunnel to curl through** — localhost is the real path the
      browser takes (§3.4).
- [ ] **Frontend up:** `npm run dev` in `frontend/`.
- [ ] **Confirm the page origin is in the backend's `CORS_ORIGINS`.** `npm run dev` serves 5173,
      which the stock value covers; `vite preview` serves **4173**, which it does not (§1.3, §3.4).
      A mismatch is a silent CORS failure that looks exactly like a dead backend.
- [ ] **Confirm the model pin is `gemma-4-26b-a4b-it` in both `.env.example` and `.env.local`, and
      get one real 200 back *through the backend* with a letter image.** (§0.1 — nothing else in this
      list matters if this is wrong. Note the ID: `gemma-4-31b-it` was the interim pin and is
      superseded; the pinned 26b read all three letters end to end in **8.1 s, 7.6 s, 8.7 s**.)
- [ ] **Confirm the answer came back clean — not the model's scratchpad.** (§0.3. If the spoken
      result is long and rambling, `thought: true` filtering has regressed and no retry fixes it.)
- [ ] **Confirm the returned text is the six-line shape** — `FROM:` / `ABOUT:` / `WHEN:` /
      `DEADLINE:` / `REF:` / `CONTACT:` (§0). Anything else and the agent is summarising something
      other than what you think.
- [ ] **Confirm a conversational turn comes back fast** — ask the agent anything and time it. Expect
      ~2 s on `gemma-4-26b-a4b-it` (§0.2). If it takes 20 s+, check the pin: a turn that slow is the
      signature of `gemma-4-31b-it`, not of a healthy build.
- [ ] **Confirm `read_document`'s `response_timeout_secs` is 120** in
      `agent/tools/read_document.json`, so the backend's own 60 s bound fires first and you control
      the failure message. (§3.3G. **Do not "fix" `LLM_TIMEOUT_MS=8000` into the vision path** — a
      healthy read exceeds it.)
- [ ] Laptop on mains. Hotspot phone charged, hotspot **on and joined once**.
- [ ] Join venue wifi, **5 GHz**. Clear any captive portal.
- [ ] **Two** full end-to-end runs with the real printed letter — not one. One result is one
      sample, and the figure you care about is end-to-end rather than note 08's model-call time.
      Check `latency-*.jsonl` and write tonight's actual numbers on your card; they are what you
      rehearse the narration against.
      - **~8 s is normal, and 14–30 s is within the measured tail** (5.1, 5.5, 8.2, 14.4, 30.5 s —
        §0.2). If a read takes 40 s+ or fails, suspect the pin first (`gemma-4-31b-it` looks exactly
        like this) and the frame upload second.
      - **Switch to the hotspot if the *conversational* turns are slow**, or if the frame upload
        itself is slow. Those are network — and since encoding plus upload is roughly half of the
        measured ~8 s (§3.3G), the network is a large share of the read.
      - If **both** runs fail outright, that is close to conclusive: the pinned model went 19/19
        across note 08 §§6.1 and 10 and 3/3 end to end through the backend, so two failures is a
        broken setup, not bad luck. Check the pin, `GET /health`, and `CORS_ORIGINS` against the page
        origin before you blame the model, and re-read §3.1a.
- [ ] If the session will not connect, test `webRtc.iceTransportPolicy: "relay"` (§3.3).
- [ ] Walk to the **back of the room** and look at the projected screen. If you cannot read the
      caption line, fix it now with `Ctrl` `+`.
- [ ] Walk the room and find the light. Decide which way the laptop faces (§2.2) — camera away from
      the projection screen and any window.

### T-10 minutes

- [ ] Windows checklist §1.4, items 1–16. **Especially #15, the audio output device.**
- [ ] Plug in the projector. Confirm the resolution Windows chose. Re-check the viewport.
- [ ] Launch Chrome: `--app=http://localhost:5173 --start-fullscreen --user-data-dir="C:\demo-profile"`.
- [ ] **Grant camera and microphone permission now, before you stand up** — and confirm no dialog
      appears when you start the session. `[REPO]` The camera matters as much as the mic here:
      `read_document` takes no parameters and reads whatever the camera sees *now* (§0), so a
      camera the browser has not been granted is a dead demo, not a degraded one. §1.3's persistent
      `C:\demo-profile` is what makes this stick.
- [ ] **Confirm laptop volume is up and the external speaker is live** if the room is bigger than 20
      people (§1.5). Then: headset mic on, say one sentence, confirm it comes out of the room PA and
      not the laptop.
- [ ] **Validation run:** one complete `read_document` with the printed letter (§3.3H) — two if the
      quota allows, because the thing you are sampling has a tail. It confirms the chain; it does
      **not** make the next call faster.
- [ ] Fallback recording open in VLC, paused at frame 0.
- [ ] Park the mouse in a corner. Do not touch it again.

### T-1 minute

- [ ] Both printed copies of letter 01 stacked, face up, on stiff card, within arm's reach.
- [ ] Connection status reads **Connected**.
- [ ] Do not disturb **on**. Phone silent — it is your hotspot, so silent, not off.
- [ ] Section B script card in hand — **the reworked one**, with the hook moved to *during* the read.
      There is no longer an A/B/C choice: the 90-second script runs live, read included (§0.2).
- [ ] **Your abandon time written on the card: 35 seconds** from the agent's "let me read that for
      you" (§3.1a — a healthy read is ~8 s, the measured tail reaches 30.5 s, and the backend gives
      up at 60 s). **Not 15 s** — that would abandon reads that were going to land. And the
      throwaway-question line — *"and while that's going, can you still hear me?"* — written next to
      it, so you do not have to invent it under pressure.
- [ ] **Two stoppable narration blocks ready, not one.** Thirty-five seconds is a long time to fill
      and the tail is real (§3.1a).

### 5.1 What to have open, in what order

| Position | What | State |
|---|---|---|
| Foreground | Chrome, `--app` fullscreen, `http://localhost:5173` | The demo. Nothing else in this window. |
| `Alt`+`Tab` 1 | VLC with the fallback recording | Paused at frame 0, fullscreen-ready |
| `Alt`+`Tab` 2 | Terminal: **backend** (`uvicorn`) | Visible logs — the §3.1a discriminator. You are looking for the inbound `POST /read_document`. |
| `Alt`+`Tab` 3 | Terminal: **frontend** (`npm run dev`) | Visible, so you can see it if it dies |
| ~~Second tab with the pre-generated `.ics`~~ | **NOT BUILT** — `add_event` does not exist (§0). Nothing to pre-generate and nothing to fall back to. | — |
| ~~Terminal: tunnel~~ | **There is no tunnel** (§3.4). Nothing to watch. | — |
| Not open | Everything else | Slack, Teams, Discord, Outlook, Steam, OneDrive: **quit** |

### 5.2 What to have printed, in what order

`docs/submission.md` Section B is right that **letter 01 (hospital appointment) is the demo** — and
right that you need **two copies**, the second face-down, because a crease across the date line ends
the demo. Reprint both at the §2.4 point sizes, on matte paper, mounted on stiff card.

Optional extras, if a judge lingers at the table:

1. **Parking penalty (02)** — the strongest *second* letter. Two amounts and two deadlines, and
   "seventy pounds, but thirty-five if you pay by the sixteenth of October" is the line that proves
   the extraction is structured rather than a transcript.
2. **School trip consent (03)** — drop this one if short on time. Longest, densest, smallest type,
   and the consent slip at the page bottom is the hardest thing on the pile for a webcam.

**Do not shuffle paper on stage** — handling noise goes straight into a close mic and can trigger
barge-in.

### 5.3 If X breaks, say Y

Section B has the per-segment lines. These are the cross-cutting ones it does not cover.

| X | Say Y | Then do |
|---|---|---|
| **Long silence after "let me read that for you"** | *(say nothing about it — keep narrating)* | **~8 s is the healthy read and the tail runs to 30.5 s (§0.2), so ten seconds of silence is normal.** Finish your narration block, start the second one, use the throwaway question (§3.1a) to check without stopping. **Cut at 35 s, not earlier and not later.** |
| **The read failed almost instantly** — a second or two, far too fast to be a model call | *"That's our local backend, not the model — one second."* | **Speed is the diagnosis** (§3.1a row 1): the process is down, on the wrong port, or the origin is not in `CORS_ORIGINS`. You will not fix any of those on stage. Go to the recording. |
| **35 seconds and still nothing** | *"That's past where a read lands — about eight seconds, measured, with a tail. Something upstream has gone. Let me give it a cleaner shot."* | Second printed copy, flatter, closer. **One** retry — budget another ~8 s for it, so only take it if you have the time left. |
| **You run out of things to say before the read lands** | *"I'll let that keep working while I tell you where this goes next —"* | Pivot to the "What's next" material (multi-page letters, a phone number, returning-sender memory). Have ~30 seconds of it ready. This is why Section B gives you three stoppable narration blocks. |
| **Agent reads a long rambling monologue** about what it is thinking | *"That's the model's scratchpad leaking through — one for the backlog."* | Interrupt it immediately; barge-in is right there. **No retry fixes this** — it is unfiltered `thought: true` parts (§0.3), a backend bug. Go to the recording. |
| Agent is **confidently wrong** about the letter | *"That's the failure we care most about — the read failed and the agent wasn't told. Let me show you what it does wired correctly."* | Switch to the recording. Naming the §3.2 footgun honestly reads far better than looking confused — and it is the exact thing the skill file exists to prevent. |
| **Conversational turns are also slow** (the agent takes 20 s+ to answer anything, not just to read) | *"Conference wifi — give me one second."* | The pin has reverted to `gemma-4-31b-it`, or the network is gone (§3.1a). Either way the demo is over as a live demo: go to the recording. Do not wait it out. |
| Agent cuts off mid-word, then silence | *"Lost the voice session — live over conference wifi."* | One reconnect, ~5 s. Then the recording. |
| Agent keeps cutting itself off | *(don't flag it)* | Audio feedback (§1.5). Drop the PA volume or go push-to-talk. |
| Nothing responds, everything looks fine | *"Conference wifi. Switching to my hotspot."* | Switch. **The switch is structurally free** (§3.4): the backend is on localhost, so there is no URL to re-register, and the page origin never changes, so the mic and camera grants survive. |
| No sound at all | *"One second — audio output."* | Settings → Sound → output device. It switched to the projector on HDMI (§1.4 #15). |
| Mic **or camera** permission dialog appears on stage | *"Fresh profile, fresh permission."* | Accept. §1.3's persistent profile and the T-10 grant prevent it. The camera is the one that ends the demo if denied — `read_document` has no parameters and reads whatever the camera sees now (§0). |
| **A judge asks about an `.ics` file, a calendar entry, a reminder or a drafted reply** | *"Not built — `read_document` is the one tool that exists today. The scaffolding for the others is designed, not wired."* | **Do not improvise a demo of them** (§0). Say what is built, which is a correct and verbatim read on 3/3 letters, and move on. |
| Screen dims or a notification pops | Keep talking, do not apologise | Dismiss. §1.4 items 8, 10–12 prevent it. |
| Text too small from the back | *(say nothing)* | `Ctrl` `+` twice. Works only if you sized in `rem`, not `vh` (§1.1). |

---

## Appendix A — Changes recommended but NOT made

Per scope, this document is the only file I wrote. Everything below is a recommendation. Items
already on the `docs/submission.md` Section D checklist are marked ⟳ — this is corroboration, not a
second opinion.

**Backend — not config, and not optional. These four are ahead of everything below:**

0a. ✅ **DONE — Filter `thought: true` parts.** `backend/app.py`'s `_extract_text()` does this, and
   the vision call runs `thinkingLevel: "minimal"` as a first layer. (§0.3)
0b. ✅ **Do NOT implement the split model paths.** Note 08 §10 retired them: `gemma-4-26b-a4b-it`
   serves conversation (2.0 s median, 8/8) and vision (3.7–4.5 s raw model call, 3/3).
   `CHAT_MODEL` and `VISION_TIMEOUT_MS` stay commented out in `.env.example`. (§0.2)
0c. ✅ **MOOT — do not strip markdown fences, there is no JSON to parse.** `backend/app.py` returns
   six plain `FROM:`/`ABOUT:`/… lines, not a structured object, so `responseSchema`'s silent
   failure (§0.4) is not on the live path. **The nine-field contract in
   `skills/letter-reader/references/output-schema.md` is aspirational, not implemented** — if
   anyone wires it up, §0.4 becomes live again and fence-stripping plus server-side validation
   comes back with it.
0d. ⟳ **STILL OPEN — serial requests, retries, honour `RetryInfo.retryDelay` as a floor.** `[REPO]`
   `backend/app.py` contains **no 429 handling and no retry at all** — grep finds no `429`, no
   `retry`, no `sleep`. Serial-ness is free with one presenter and one tool, so concurrency is not
   a live risk. The missing 429 retry is: it is the likeliest single failure on the day (§3.1 row
   4a), and right now a 429 surfaces to the presenter as a failed read. **For the MVP that is an
   acceptable trade** — one retry is the recovery and §5.3 has the line — but know that the backend
   is not doing it for you.

**Before demo day, config only, highest value per minute:**

1. ✅ **DONE — the Gemma model pin** is `gemma-4-26b-a4b-it` in `.env.example`, and a real 200 has
   come back *through the backend* on all three letters (8.1 / 7.6 / 8.7 s). Confirm `.env.local`
   matches and re-run at T-60 on the venue network. (§0.1)
2. ⟳ **STILL OPEN — `tool_error_handling_mode: "summarized"` on `read_document`**, the one tool
   there is. `[REPO]` Not set in `agent/tools/read_document.json`. **Prevents the agent inventing a
   letter summary when `read_document` fails** — a hidden failure is still the worst thing this
   build can do. (§3.2)
3. ✅ **DONE — `pre_tool_speech: "force"` on `read_document`**, along with
   `tool_call_sound_behavior: "always"` and `interruption_mode: "allow"`. It covers a ~8 s silence
   and is an accessibility requirement as well as latency cover. (§3.3F, §4.5)
3b. ✅ **Leave `response_timeout_secs` at 120**, which is what `agent/tools/read_document.json`
   already sets. Against a measured ~8 s read with a 30.5 s tail and a 60 s backend bound, 120 is
   the right value — the backend still fails first and controls the message. Earlier drafts arguing
   for the 20 s default were comparing against the raw model call. (§3.3G)
3c. **NEW — add `soft_timeout_config.message`.** At ~8 s with a tail to 30.5 s, a mid-wait
   reassurance is warranted after all; earlier drafts dropped it on the strength of a four-second
   figure. (§3.3F, §4.5)
4. ⟳ Enable `interruption` under Advanced → Client Events — **and add `agent_chat_response_part`**,
   which is off by default in voice conversations and silently kills captions. (§4.4) Note that
   `interruption_mode: "allow"` is already set on the tool, so barge-in during the read is covered;
   this item is about the client event the UI needs.
5. `turn_eagerness: "patient"` with a generous `turn_timeout`. (§4.5)
6. ~~Reserved tunnel hostname, with the webhook tool URL pointed at it.~~ **RETIRED — there is no
   tunnel and no webhook tool.** `read_document` is a client tool; the browser calls localhost.
   (§3.3A, §3.4)
7. ⟳ Add the explicit failure instruction to the **system prompt text** in
   `agent/persona-prompt.md`, not just its operating-rules prose. (§3.2)

**Code:**

8. `.env.local`: add `http://localhost:4173` to `CORS_ORIGINS` if presenting from `vite preview`.
   (§1.3, §3.4 — and with no tunnel, a CORS mismatch is now one of the few remaining ways the
   browser fails to reach the backend, so this is a T-60 check rather than a nicety.)
9. ✅ **Leave `LLM_TIMEOUT_MS` out of the vision path, which is what `backend/app.py` already
   does** — a healthy end-to-end read is 8.1–8.7 s and would breach an 8 s gate. The call is bounded
   by `httpx.Timeout(60.0, connect=10.0)`. Do not add `VISION_TIMEOUT_MS`. **The live item here is
   the frame:** downscale to ≤250 KB before upload, because encoding plus upload of a ~0.5 MB PNG is
   roughly half the measured ~8 s and is the biggest latency win left (§3.3G).
10. ⟳ `frontend/index.html`: `<title>LetterLens</title>`. (§4.2)
11. A `?demo=1` root font-size override rather than restyling everything. (§1.1)
12. A `?mock=1` flag setting `toolMockConfig: { mockingStrategy: "selected", mockedToolNames: ["read_document"] }`. (§3.3I)
13. An "upload a photo instead" input path — product feature and lighting/network fallback in one. (§2.3)
13b. A clear on-screen **`Reading your letter…`** state for the duration of the call — ~8 s, tail to
    30.5 s (§0.2) — in the polite live region. At that length it is not a nicety: it is what makes
    the pause legible as work to a screen-reader user, and it is a §3.1a discriminator for you.
    (§0.2, §3.1a, §4.1)

14a. **NOT BUILT, and out of scope for this MVP: `draft_reply`, `add_event`, `set_reminder`.** No
    endpoint, no client-tool registration, no `.ics`, no calendar card, no reminder card (§0).
    Listed here so the gap between what the docs describe and what runs is on the record rather
    than discovered on stage.

**`test-letters/generate.py` (not modified here — and ⚠️ *apparently already modified by someone
else*: `DPI = 300`, `W, H = 2480, 3508` and an overflow check are now in the file, so items 16 and
18 look done and 14, 15 and 17 need re-checking against the new render rather than the measurements
in §2.4):**

14. Body 16–18 pt, key-box values 20–22 pt, deadline line 24 pt bold. (§2.4)
15. Box labels from `(90,90,90)` to full `(26,26,26)` ink. (§2.4)
16. Render at 300 DPI — `W, H = 2480, 3508`, all sizes doubled. (§2.4)
17. Widen the text measure past `wrap=62` to reclaim the blank right third. (§2.4)
18. Add a bottom-margin / overflow assertion — all three letters already run to within millimetres of
    the page edge, and enlarging the type will push content off silently. (§2.4)

## Appendix B — Sources consulted

**Working tree, 2026-10-03** (the revision pass that removed the tunnel architecture):
`backend/app.py`, `frontend/src/App.tsx`, `agent/tools/read_document.json`, and live calls against
the running backend — `GET /signed-url` (200 in 1.4 s, real token) and `POST /read_document` with
each of the three `test-letters/` PNGs (200 first attempt, 8.1 / 7.6 / 8.7 s, verbatim-correct
against the known-good `.txt` transcripts). The 5.1 / 5.5 / 8.2 / 14.4 / 30.5 s tail is recorded in
`backend/app.py`'s own comments.

**Repository** (commit `39b8655`, the original pass): `agent/persona-prompt.md`, `.env.example`, `.gitignore`,
`frontend/` (`index.html`, `package.json`, `src/App.tsx`, `src/main.tsx`, `src/index.css`,
`src/App.css`, `vite.config.ts`), `backend/requirements.txt`, `test-letters/generate.py` and the
three rendered PNGs, `skills/letter-reader/SKILL.md`, `docs/submission.md`.

Per instruction, **`.env.local` was not read** and no key value appears anywhere in this file.

**Research notes**, all citing primary sources fetched 2026-10-03:
`docs/research/03-elevenlabs-server-tools-and-variables.md` (§§1.3, 1.4, 7, 8, plus the independent
verification pass added in `39b8655`), `docs/research/04-elevenlabs-react-sdk.md` (§§3.4, 6.4, 6.6,
7.1, 7.2, 9.1, 9.2, 9.3, 10), `docs/research/07-gemini-vision-and-structured-output.md` (§§2.4, 2.6),
and `docs/research/08-gemma-live-api-test-results.md` (§§1, 1.1, 1.2, 2, 3, 4, 5, 6, 6.1, 7, 8, 8.1,
8.3, 10) — the last of which is **live HTTP against a real key rather than documentation**, and which
supersedes note 01 on the model pin and the image transport while, in §10, confirming rather than
overturning the 8-second latency budget. Where this file and
note 01 disagree, note 08 wins; the places that changed are called out inline (§§0.1, 0.2, 2.4,
3.3G, Appendix A item 9).

**Web**, fetched 2026-10-03 — webcam field of view and fixed-focus range:
- [B&H — computer/USB webcam listings](https://www.bhphotovideo.com/c/buy/computer-camera-hd-usb-webcams/ci/6499/pn/5)
- [B&H — JLab GO USB Webcam specifications](https://www.bhphotovideo.com/c/product/1795578-REG/jlab_wgocamrblk124_go_usb_webcam_black.html)
