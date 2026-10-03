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
which overturned the model pin, the latency budget and several assumptions that were load-bearing
for this file. The revised material is §§0.1–0.4, 3.1a, and the marked passages in §§1.5, 2.4, 3.1,
3.3, 4.5, 5 and Appendix A. **Where this file and the docs-based notes 01 and 07 disagree, note 08
wins.**

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

`[REPO]` At commit `39b8655`, matching what `docs/submission.md` Section D already records:

- `frontend/src/App.tsx` is **the unmodified Vite + React starter** — counter button, Vite and React
  logos, links to Discord and Bluesky. No camera, no transcript, no conversation UI.
- `frontend/package.json` dependencies are **`react` and `react-dom` only**. No `@elevenlabs/react`.
- `backend/` contains **only `requirements.txt`**. No FastAPI app, no webhook handlers.
- `agent/persona-prompt.md` references `agent/*.json`; **no such file exists.**
- `frontend/index.html` has `<title>frontend</title>`.

So §1 and §4 below are **requirements to build against**, not an audit of something that exists.
§2 and §3 are real right now, because the printed paper and the venue network do not care whether
the app is finished.

### 0.1 The model pin — **FIXED**

`[REPO]` `.env.example` now pins `GEMMA_MODEL=gemma-4-31b-it` and
`GEMMA_VISION_MODEL=gemma-4-31b-it`, with a comment citing
`docs/research/08-gemma-live-api-test-results.md` §2 and noting that vision is verified working on
that ID specifically. It also stages two commented-out lines for the split-path architecture
(§0.2): `#CHAT_MODEL=gemini-2.5-flash-lite` and `#VISION_TIMEOUT_MS=90000`, inert until the backend
reads them.

**What it used to be, and why it mattered.** Both values were `gemma-3-27b-it`. `[RESEARCH]` Note 08
§2 records the live result: a flat **404**, verbatim *"models/gemma-3-27b-it is not found for API
version v1beta, or is not supported for generateContent"*. The repo's defaults could never have
worked on any request. Earlier drafts of this file and of `docs/submission.md` said the fix was
`gemma-4-26b-a4b-it`, following note 01's recommendation; **that is superseded.** Note 08 verified
vision specifically on `gemma-4-31b-it`, and the 26B MoE's apparent speed advantage came from a
confounded test (`maxOutputTokens: 1`), which note 08 §6.1 says explicitly should not be used to
pick a model. `gemma-4-26b-a4b-it` remains useful as a second 30 RPM quota bucket, since the free
tier is scoped per project *per model*.

**What is still open.** The pin is right and the model works at the API level, but **nobody has made
a `read_document` call through the application stack**, because the backend does not exist yet. The
demo-day consequence of a bad pin has not changed: `read_document` fails on every single attempt, in
a way that looks exactly like a network failure from the stage, and you burn the whole "if it
breaks" budget on a problem no amount of re-holding the letter can fix. **Get one real 200 through
the backend, with a real frame, before demo day.** Item 1 in the T-60 checklist. Per instruction I
did not read or touch `.env.local` — check the pin there too.

`[REPO]` Two good signs already in `.gitignore`: `captures/` and `latency-*.jsonl`. **Ship the
latency log.** With a model that takes 20–57 seconds (§0.2) this stops being nice-to-have: it is the
only thing that tells you at T-60 what your actual distribution looks like tonight, rather than
finding out mid-script.

### 0.2 The read is slow and fails half the time — plan the demo around it

`[RESEARCH]` This is the single biggest change since this document was first written, and it reaches
into every other section. Note 08 is **live HTTP against a real key**; every figure below came off
the wire on 2026-10-03.

| Measurement | Value |
|---|---|
| Successful Gemma latency, trivial text | **19.9 – 35.1 s** |
| Structured extraction | **42.6 s** |
| **Vision, on our own `test-letters/01-hospital-appointment.png`** | **56.8 s** |
| Failure rate, **strictly serial**, well inside the 30 RPM free-tier quota | **~50 %** (6 of 12 succeeded) |
| Failure rate at 10-way concurrency | **26 of 40 returned `500 INTERNAL`** |
| Calls that completed inside 8 s | **zero** |

Three consequences, in order of how much they will hurt you:

1. **`LLM_TIMEOUT_MS=8000` cannot hold for a Gemma call.** Not "is tight" — *cannot hold*. Every
   success exceeded it. The human has adopted note 08 §7 **option 1, split the paths**: fast
   conversational turns on `gemini-2.5-flash-lite` inside the 8 s budget, and `read_document` on
   `gemma-4-31b-it` with `VISION_TIMEOUT_MS=90000` and a spoken *"let me read that for you, one
   moment"* covering the wait. The point is containment — a slow or failed read degrades **one
   feature** instead of the whole conversation, so the agent can still talk to you and apologise.
2. **A long silence is now NORMAL, which is a demo-operations problem** (§3.1a). You can no longer
   tell a healthy read from a dead backend by waiting, so you need discriminators and a pre-agreed
   abandon time.
3. **Retries are mandatory, and they are expensive.** At a ~50 % per-call failure rate you will
   retry roughly every other read, and a retry costs another 20–57 s. Two consecutive failures is a
   ~25 % event. `docs/submission.md` Section B now budgets the demo at ~2 minutes rather than 90
   seconds because of this; read that reality box before you rehearse.

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
regardless. Note 01's recommended alternative — a single forced function call — is listed **PENDING
/ unverified** in note 08 §8. Do not count on it before demo day.

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
  `--app=` removes the omnibox — so the tunnel URL never appears on the projector — and the tab strip.
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
  afford to lose, and which you will have just spent forty-five seconds waiting for.
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

`[RESEARCH]` **That trade has got much worse since note 07 was written, and it changes the ranking.**
Note 08 §3 measured a 185 KB full-page scan at **258 image tokens** and a wall-clock of **56.8 s** —
and the same call spent 1,109 *thought* tokens to emit a 5-token answer, so latency is dominated by
reasoning, not by pixels. Two things follow. First, image tokens are cheap, so there is no token
argument against sending a legible frame. Second, there is no latency headroom left to spend on
`mediaResolution`: at 57 s you are already past what the demo can absorb (§0.2). **Fix it on the
paper and in the frame, where it is free, and leave `mediaResolution` alone until somebody has
tested `thinkingConfig` (note 08 §8, pending) and bought the latency back.**

Recommendations:

- **Reprint larger. Do not bother raising contrast** — it is already 17:1 where it matters.
- **Point sizes for an A4 demo print:** body **16–18 pt**, key-box values **20–22 pt**, the headline
  deadline line **24 pt bold**, letterhead 28–32 pt. That puts body x-height at ~9–10 px at 1080p —
  at the floor rather than well under it.
- **Fix the two grey tones.** Box labels at 6.3:1 and the strapline at 6.2:1 are the lowest-contrast
  ink on the page and the first to dissolve under a webcam in poor light. Make the box labels full
  `#1a1a1a`. They are the words "Date", "Time", "Pay reduced amount by" — exactly the semantics
  `read_document` must land, and exactly the fields
  `skills/letter-reader/references/output-schema.md` governs.
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

> **⚠️ The premise of this section has changed.** It used to be safe to read "dead air" as "something
> broke". It is not any more. Per §0.2, a **healthy** read is 20–57 seconds of silence and fails
> outright about half the time, so **a long pause is now the normal case and not a signal.** Every
> row below has been re-read with that in mind, and §3.1a is new: it is how you tell a slow read
> from a dead one without guessing.

### 3.1 The failure table

| # | What breaks | What the audience sees/hears | Presenter's next 5 seconds |
|---|---|---|---|
| 0 | **Nothing. The read is just slow.** | A long silence after the agent says "let me read that for you". **Indistinguishable from #1, #4 and #5 from the audience's seat, and often from yours.** | **Keep narrating.** This is the default assumption until your abandon time (§3.1a). Do not touch anything, do not reach for the keyboard, do not say "hmm". |
| 1 | **Tunnel drops or restarts** (`PUBLIC_BASE_URL`) | Greeting fine, then after you hold the letter up: a silence that **never ends**, or — worse — a confident summary of a letter it never read. See 3.2. | Stop it talking. *"That's the webhook, not the model — our backend tunnel just dropped."* Go to the recording. Do not debug on stage. |
| 2 | **ElevenLabs session drops mid-sentence** | The agent **cuts off mid-word**. Silence. | *"We just lost the voice session — this is live over conference wifi."* One reconnect attempt, ~5 s. Then the recording. |
| 3 | **Vision call fails or times out** against `VISION_TIMEOUT_MS` | A long gap — up to the full 90 s — then the agent says it could not read the letter and gives one physical instruction. | Section B's line still covers this and it is still the right one. Use the **second printed copy**, flatter, closer. **One** retry, and know that the retry costs you another 20–57 s. |
| 4 | **Congested wifi / captive-portal re-auth** | Everything *looks* connected. Nothing responds. Long pauses everywhere — **including on the conversational turns, which is the tell** (§3.1a). | *"Conference wifi. Switching to my hotspot."* Switch (pre-tested — 3.3C). If the tunnel URL changes you are now in failure #1 unless you reserved a hostname. |
| 5 | **The model's scratchpad reaches the agent** (§0.3) | The agent starts speaking and does not stop — rambling, self-correcting, nothing like a letter summary. | Interrupt it. *"That's the model's scratchpad leaking through — one for the backlog."* **No retry will fix this**; the bug is in the backend. Go to the recording. |

Failure #3 is still the one to relax about — the *behaviour* is good even though the wait is long:
`skills/letter-reader/SKILL.md` has a whole **"When the image is unusable"** branch that picks one
concrete physical instruction — closer, flatten, tilt, turn, steady — and caps retries at three
before suggesting a trusted person. That is designed behaviour, and Section B is right that you
should sell it rather than apologise for it. What has changed is the *arithmetic*: three retries at
20–57 s each is up to three minutes, so the skill's retry cap is a product behaviour, not a demo
plan. **On stage you get one retry.**

### 3.1a Telling a slow read from a dead one — the discriminators

This is the new skill demo day demands of you. A 45-second silence is the healthy case. You need to
know, without stopping and without touching the laptop, whether to keep talking or to cut.

**Set an abandon time before you stand up. Use 75 seconds** — comfortably past the 56.8 s vision
measurement, inside the 90 s `VISION_TIMEOUT_MS`, and short enough that you still have an audience.
Start counting from the moment the agent says *"let me read that for you"*, not from when you raised
the letter. **Below 75 s you narrate. At 75 s you stop and run the recovery line, regardless of what
you believe is happening.** The value of a pre-committed number is that it removes the decision from
the worst possible moment to be making one.

What to look at while you wait, in order of how much it tells you:

| Signal | Healthy slow read | Something is actually broken |
|---|---|---|
| **The agent's spoken "let me read that for you" at the start** | **Played.** The tool call reached the agent and the agent acted on it. | **Never played.** The agent never started the tool call — that is a session or config problem, not a slow model. Do not wait out the 75 s; you are waiting for nothing. |
| **The on-screen `Reading your letter…` state** | Up and stays up. | Never appeared, or it appeared and then cleared with no spoken result — the latter means the tool returned and something downstream ate the answer. |
| **Ask the agent a throwaway question** — *"and while that's going, can you still hear me?"* | **It answers, fast.** The conversational path is on `gemini-2.5-flash-lite`, a different model and a different quota bucket, so it is unaffected by the slow read. **This is the single best discriminator you have**, and it is the whole payoff of the split architecture (§0.2). | **Silence.** The session or the network is gone, not the model. Stop waiting and go to recovery. |
| **Tunnel terminal** (`Alt`+`Tab` 4, §5.1) | Shows the inbound request, no response yet. | Shows a disconnect, or no inbound request at all — the latter means the webhook never arrived. |
| **Backend terminal** (`Alt`+`Tab` 3) | One in-flight Gemma request, waiting. | A 500/429 and a retry in progress (fine, but add 20–57 s to your estimate), or a traceback (go to recovery). |

**Use the third row.** It is the only one that works from where you are standing, it costs five
seconds, it sounds completely natural to the room, and it cleanly separates "the slow thing is slow"
from "everything is dead". Build it into the script as a line you *may* use, so it does not sound
improvised when you do.

**Do not** reach for the keyboard, refresh, or peer at a terminal while the room watches. Every one
of those reads as panic, and four times out of five you would have been interrupting a healthy read.

### 3.2 Failure #1 deserves its own warning

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

For LetterLens: **if `read_document` fails, the agent is not told, and will invent a letter
summary** — in a demo of an assistive product for blind people, in front of judges, about a date
someone would act on. It is the exact failure
`skills/letter-reader/SKILL.md` spends three sections forbidding, arriving through a channel the
skill cannot see.

**`tool_error_handling_mode: "summarized"` on every webhook tool, before demo day.** It is already
on the `docs/submission.md` Section D checklist. Tick it.

`[RESEARCH]` Reinforce it in the prompt too. Note 03 flags: *"What the agent literally says on
timeout/failure: UNCONFIRMED. No doc page states a canned phrase."* `agent/persona-prompt.md`'s
operating rules say the right thing in prose but **the system prompt text itself does not** — which
`docs/submission.md` also flags as recommendation 4. The prompt cannot act on an error it never
receives, and it cannot follow a rule that lives only in a Markdown heading above it.

### 3.3 Mitigations, ranked, with a hard line between "before" and "on the day"

#### MUST be prepared before demo day — cannot be improvised

**A. A reserved tunnel hostname.** `[PRACTICE]` A free ngrok quick tunnel gets a **new random
subdomain every restart**; `cloudflared --url` gets a new random `*.trycloudflare.com` every run.
`[RESEARCH]` Note 03 §1.4 records `api_schema.url` as a **required** field configured server-side on
the agent, so every tunnel restart invalidates the configured webhook URL and you must re-edit it in
the dashboard or via the API. On stage that is 2–5 minutes you do not have. Use an ngrok reserved
domain or a named Cloudflare tunnel, point the tool at it once, never touch it again. **You cannot
register a domain and propagate DNS in the 10 seconds after it breaks.**

**B. A pre-recorded screen capture of a successful end-to-end run.** `[PRACTICE]` With audio, shot on
this laptop at the projector's resolution, **stored as a local file** (not YouTube — you will have no
network), open in VLC, paused at frame 0, one `Alt`+`Tab` away. The only mitigation that works when
the network is simply gone, and the only way to deliver Section B's "total collapse" line with
something to show. `docs/submission.md` Section D already wants a demo video for the submission form
— **record it so it doubles as this.** You cannot record a successful run during a failed demo.

**C. A phone hotspot, tested end-to-end.** `[PRACTICE]` Not "I have a hotspot" — SSID saved, laptop
joined at least once, data allowance confirmed, and **the full chain exercised over it**: tunnel up,
agent connects, `read_document` round-trips. First-time joining on stage costs 60–90 seconds and
usually restarts your tunnel, dropping you into failure #1.

**D. The model pin, verified with a real 200 *through the backend*.** See §0.1. The pin itself is
fixed and the model is proven at the API level; what is not proven is the application path to it.
No network mitigation saves you from a `read_document` handler that has never returned a letter.

**D2. The split model paths, actually implemented.** §0.2. This is a mitigation, not just an
architecture note: if conversational turns still go to Gemma on the day, **every single turn costs
20–57 s**, the agent cannot answer the throwaway question that §3.1a depends on, and you lose both
the demo and your ability to diagnose it. `CHAT_MODEL=gemini-2.5-flash-lite` and
`VISION_TIMEOUT_MS=90000` are staged commented-out in `.env.example`; they do nothing until the
backend reads them.

**D3. `thought: true` filtering in the backend.** §0.3. Three lines of Python standing between you
and the agent reading four thousand characters of model deliberation aloud to the room.

#### Cheap, and still before demo day

**E. `tool_error_handling_mode: "summarized"`.** §3.2. Minutes of work. Prevents the worst outcome.

**F. Cover the latency with speech.** `[RESEARCH]` Note 03 §1.3, verbatim: `pre_tool_speech` —
"'auto' (default) decides based on recent tool latency, **'force' always asks the agent to speak**,
'off' fully opts out". Set `"force"` on `read_document`. `[RESEARCH]` Also available:
`tool_call_sound` (`typing`, `elevator1`–`4`), and note 04 §7.2's
`conversation_config.turn.soft_timeout_config` with a `message` field — "Message to show when the
first soft timeout is reached while waiting for LLM response." Section B's script hangs its entire
timing on the agent saying *"let me read that for you, one moment"* at ≈0:14; `pre_tool_speech:
"force"` is what makes that line actually happen.

**This has gone from a polish item to a load-bearing one.** The pause it covers is no longer the
twelve seconds the original script assumed — it is **20–57 seconds** (§0.2). Without that spoken
line you are standing in up to a minute of unexplained silence with nothing to point at, and
§3.1a's first and best discriminator ("did the line play?") does not exist. It is also an
**accessibility** requirement (§4.5): silence tells a blind user nothing, and forty-five seconds of
it tells them the product is broken. `soft_timeout_config.message` is worth setting as a second
layer for the same reason — a 45-second wait justifies a second reassurance partway through, not
just one at the start.

**G. Get the two timeouts and the frame payload right.** This one has changed substantially.

`[REPO]` `.env.example` sets `LLM_TIMEOUT_MS=8000`, and under the split-path architecture (§0.2)
**that value is now the *chat* budget only** — correct for a conversational turn on
`gemini-2.5-flash-lite`, and still correctly sitting inside the webhook timeout so the backend fails
first and you control the failure message. `[RESEARCH]` Note 03 §7.1 gives the webhook
`response_timeout_secs` default as **20 s** (range 5–300), re-confirmed in the verification pass as
claim 13.

**But the 20 s webhook default is now shorter than a *healthy* `read_document` call.** Measured
Gemma latency is 19.9–56.8 s (§0.2), so left at the default the platform times the tool out before
the model has answered, on every single read. The ordering that has to hold is:

```
VISION_TIMEOUT_MS (90 s)  <  read_document response_timeout_secs (≥120 s)
LLM_TIMEOUT_MS    (8 s)   <  every other tool's response_timeout_secs (20 s default, fine)
```

**Raise `response_timeout_secs` to ≥120 on the `read_document` webhook tool only.** Leave the others
alone. `docs/submission.md` Section D carries the same line.

`[CALC]` **Payload size still matters, but it is no longer the big number.** On a saturated
conference uplink of ~2 Mbps a 1.5 MB full-resolution frame takes **~6 seconds to upload before the
model sees anything**, and `[RESEARCH]` note 07 §2.4 notes base64 inflates bytes by ~4/3 on top of
that. Against a 20–57 s model call those 6 seconds are now 10–30 % of the wait rather than most of
it — still worth removing, no longer the thing to optimise first. Downscale and JPEG-compress
client-side: long edge ~1280 px, quality ~80, **target ≤ 250 KB**, keep it in colour (letterhead
colour is real signal). `[RESEARCH]` Note 08 §3 confirms `inline_data` base64 works in a single
round trip, so there is no Files API hop to budget for. Balance this against the `mediaResolution`
point in §2.4 — you want fewer bytes but not fewer *legible* pixels, which is exactly why §2.4 says
fix it on the paper instead.

**H. Validate the chain at T-10 — but do not expect it to make the model faster.** `[PRACTICE]` At
T-10, on the venue network, with the actual printed letter, run one complete `read_document` round
trip. It validates the whole chain — tunnel, agent config, webhook secret, vision call, thought-part
filtering, audio out — at the last possible moment, and it gives you one real latency sample for
tonight's network.

`[RESEARCH]` **It will not warm anything.** The latency is generation-bound, not cold-start: note 08
§1.2 attributes the 56.8 s vision call to the 1,109 thought tokens it emitted for a 5-token answer.
The second call costs what the first one cost. Do the warm run for validation, and do **two** of
them if you have time — at a ~50 % failure rate a single success tells you much less than you think
it does, and a single failure tells you almost nothing (note 08 §6: *"never conclude a capability is
unsupported from 5xx alone"*).

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

**It has, however, been promoted.** With a 20–57 s read at a ~50 % failure rate (§0.2), the mock is
no longer only a break-glass option — `docs/submission.md` Section B lists it as **option C**, a
legitimate way to fit a short slot, and it is the *only* way the 30-second cut-down can exist at
all. **The condition is disclosure:** one spoken sentence — *"the vision call is stubbed here so I
fit the slot; come to the table and I'll run it live"* — and it is completely fine. Undisclosed, in
a public repo, in front of judges, it is not. Build the flag, and build the sentence into the card
next to it.

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

### 3.4 An architecture decision that already protects you

`[REPO]` `.env.example` sets `CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173` — the
**frontend is served from localhost and only the backend goes through the tunnel**. Keep it that way.
`[RESEARCH]` Note 04 §9.2 records that `navigator.mediaDevices` needs a secure context — HTTPS or a
localhost-family origin — so `http://localhost:5173` is fine where a LAN IP would not be. More
importantly for §3: **browser permissions are per-origin.** Served through the tunnel, every tunnel
restart would be a new origin and you would lose the granted microphone permission, producing a
permission dialog live on stage on top of everything else. Serving the UI from localhost makes the
mic grant survive every network event.

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
   "Reading your letter…", "Microphone muted", "Connection lost", "Calendar file downloaded".
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
| After the `.ics` download from `add_event`, announce the filename and location | A browser download is a focus and announcement black hole. Put it in the polite live region — the agent does not say it, so no conflict. |

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
| **The agent must narrate its own waiting — and the wait is 20–57 seconds** | §0.2. Several seconds of silence tells a sighted user "it's thinking" and a blind user nothing; **forty-five seconds of it tells a blind user the product is broken**, and they have no screen to check. `pre_tool_speech: "force"` (§3.3F) fixes the accessibility problem and the latency problem with one config change. For a wait this long, also set `soft_timeout_config.message` so there is a second reassurance partway through, and make sure the on-screen `Reading your letter…` state is in the polite live region (§4.1) — it is state the agent does not speak, so there is no double-speak conflict. |
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

- [ ] **Confirm the model pin is `gemma-4-31b-it` in both `.env.example` and `.env.local`, and get
      one real 200 back *through the backend* with a letter image.** (§0.1 — nothing else in this
      list matters if this is wrong. Note the ID: `gemma-4-26b-a4b-it` was the old recommendation
      and is superseded; vision is verified on 31b.)
- [ ] **Confirm the answer came back clean — not the model's scratchpad.** (§0.3. If the spoken
      result is long and rambling, `thought: true` filtering is missing and no retry fixes it.)
- [ ] **Confirm a conversational turn comes back fast** — ask the agent anything and time it. If it
      takes 20 s+, the chat path is still on Gemma, you have no split (§0.2), and §3.1a's best
      diagnostic does not work.
- [ ] **Confirm `read_document`'s webhook `response_timeout_secs` is ≥120**, not the 20 s default.
      (§3.3G — the default is shorter than a healthy read.)
- [ ] Laptop on mains. Hotspot phone charged, hotspot **on and joined once**.
- [ ] Join venue wifi, **5 GHz**. Clear any captive portal.
- [ ] Backend up. Tunnel up **on the reserved hostname**. `PUBLIC_BASE_URL` matches the URL
      configured on the ElevenLabs webhook tools.
- [ ] `curl` the backend health endpoint **through the tunnel**, not locally.
- [ ] **Two** full end-to-end runs with the real printed letter — not one. At a ~50 % failure rate
      (§0.2) a single result tells you very little. Check `latency-*.jsonl` and write tonight's
      actual numbers on your card; they are what you rehearse the narration against.
      - **20–60 s is normal.** Do not switch networks over it — the latency is the model, not the
        venue (§3.3H), and the hotspot will not be faster.
      - **Switch to the hotspot if the *conversational* turns are slow**, or if the frame upload
        itself is slow. Those are network. The read is not.
      - If **both** runs fail outright, that is a ~25 % event on a healthy setup and a ~100 % event
        on a broken one — do a third before concluding anything, and re-read §3.1a.
- [ ] If the session will not connect, test `webRtc.iceTransportPolicy: "relay"` (§3.3).
- [ ] Walk to the **back of the room** and look at the projected screen. If you cannot read the
      caption line, fix it now with `Ctrl` `+`.
- [ ] Walk the room and find the light. Decide which way the laptop faces (§2.2) — camera away from
      the projection screen and any window.

### T-10 minutes

- [ ] Windows checklist §1.4, items 1–16. **Especially #15, the audio output device.**
- [ ] Plug in the projector. Confirm the resolution Windows chose. Re-check the viewport.
- [ ] Launch Chrome: `--app=http://localhost:5173 --start-fullscreen --user-data-dir="C:\demo-profile"`.
- [ ] Confirm mic and camera permissions are already granted — no dialog appears.
- [ ] Headset mic on. Say one sentence; confirm it comes out of the room PA, not the laptop.
- [ ] **Validation run:** one complete `read_document` with the printed letter (§3.3H). It confirms
      the chain; it does **not** make the next call faster.
- [ ] Fallback recording open in VLC, paused at frame 0. Pre-generated `.ics` open in a second tab.
- [ ] Park the mouse in a corner. Do not touch it again.

### T-1 minute

- [ ] Both printed copies of letter 01 stacked, face up, on stiff card, within arm's reach.
- [ ] Connection status reads **Connected**.
- [ ] Do not disturb **on**. Phone silent — it is your hotspot, so silent, not off.
- [ ] Section B script card in hand — **the reworked one**, with the hook moved to *during* the read
      and only your chosen option (A, B or C) on it.
- [ ] **Your abandon time written on the card: 75 seconds** from the agent's "let me read that for
      you" (§3.1a). And the throwaway-question line — *"and while that's going, can you still hear
      me?"* — written next to it, so you do not have to invent it under pressure.

### 5.1 What to have open, in what order

| Position | What | State |
|---|---|---|
| Foreground | Chrome, `--app` fullscreen, `http://localhost:5173` | The demo. Nothing else in this window. |
| `Alt`+`Tab` 1 | VLC with the fallback recording | Paused at frame 0, fullscreen-ready |
| `Alt`+`Tab` 2 | Second tab with the pre-generated `.ics` | Per Section B's calendar-card fallback |
| `Alt`+`Tab` 3 | Terminal: backend | Visible logs |
| `Alt`+`Tab` 4 | Terminal: tunnel | Visible, so you can see it drop |
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
| **Long silence after "let me read that for you"** | *(say nothing about it — keep narrating)* | **This is normal.** 20–57 s is the healthy range (§0.2). Work through your narration blocks. Use the throwaway question (§3.1a) if you need to check without stopping. **Cut at 75 s, not before.** |
| **75 seconds and still nothing** | *"That one's not coming back — it fails about half the time on the free tier, which is exactly why the conversation doesn't depend on it."* | Second printed copy, flatter, closer. **One** retry — and know it costs another 20–57 s, so if you are already past time, go straight to the recording instead. |
| **You run out of things to say before the read lands** | *"I'll let that keep working while I tell you where this goes next —"* | Pivot to the "What's next" material (multi-page letters, a phone number, returning-sender memory). Have ~30 seconds of it ready. This is why Section B gives you three stoppable narration blocks. |
| **Agent reads a long rambling monologue** about what it is thinking | *"That's the model's scratchpad leaking through — one for the backlog."* | Interrupt it immediately; barge-in is right there. **No retry fixes this** — it is unfiltered `thought: true` parts (§0.3), a backend bug. Go to the recording. |
| Agent is **confidently wrong** about the letter | *"That's the failure we care most about — the read failed and the agent wasn't told. Let me show you what it does wired correctly."* | Switch to the recording. Naming the §3.2 footgun honestly reads far better than looking confused — and it is the exact thing the skill file exists to prevent. |
| **Conversational turns are also slow** (the agent takes 20 s+ to answer anything, not just to read) | *"Conference wifi — give me one second."* | The chat path is not split, or the network is gone (§3.1a). Either way the demo is over as a live demo: go to the recording. Do not wait it out. |
| Agent cuts off mid-word, then silence | *"Lost the voice session — live over conference wifi."* | One reconnect, ~5 s. Then the recording. |
| Agent keeps cutting itself off | *(don't flag it)* | Audio feedback (§1.5). Drop the PA volume or go push-to-talk. |
| Nothing responds, everything looks fine | *"Conference wifi. Switching to my hotspot."* | Switch. The reserved hostname means the tool URL survives. |
| No sound at all | *"One second — audio output."* | Settings → Sound → output device. It switched to the projector on HDMI (§1.4 #15). |
| Mic permission dialog appears on stage | *"New origin, fresh permission."* | Accept. §1.3's persistent profile prevents it. |
| Screen dims or a notification pops | Keep talking, do not apologise | Dismiss. §1.4 items 8, 10–12 prevent it. |
| Text too small from the back | *(say nothing)* | `Ctrl` `+` twice. Works only if you sized in `rem`, not `vh` (§1.1). |

---

## Appendix A — Changes recommended but NOT made

Per scope, this document is the only file I wrote. Everything below is a recommendation. Items
already on the `docs/submission.md` Section D checklist are marked ⟳ — this is corroboration, not a
second opinion.

**Backend — not config, and not optional. These four are ahead of everything below:**

0a. ⟳ **Filter `thought: true` parts.** Three lines. Without them the agent reads 4,236 characters of
   model deliberation aloud to a blind user. (§0.3)
0b. ⟳ **Implement the split model paths** — `CHAT_MODEL=gemini-2.5-flash-lite` for conversation,
   `gemma-4-31b-it` + `VISION_TIMEOUT_MS=90000` for `read_document`. Staged commented-out in
   `.env.example` and inert until the backend reads them. (§0.2)
0c. ⟳ **Strip markdown fences before parsing, and validate server-side.** `responseSchema` returns
   200 and is silently ignored. (§0.4)
0d. ⟳ **Serial requests, mandatory retries, honour `RetryInfo.retryDelay` as a floor.** (§0.2)

**Before demo day, config only, highest value per minute:**

1. ⟳ **The Gemma model pin — ✅ already fixed** to `gemma-4-31b-it` in `.env.example`. Confirm
   `.env.local` matches, then get one real 200 *through the backend*. (§0.1)
2. ⟳ `tool_error_handling_mode: "summarized"` on every webhook tool. **Prevents the agent inventing a
   letter summary when `read_document` fails** — and with a ~50 % failure rate it *will* fail. (§3.2)
3. ⟳ `pre_tool_speech: "force"` on `read_document`. Load-bearing now, not polish: it is the only
   thing covering a 20–57 s silence. (§3.3F, §4.5)
3b. ⟳ **`response_timeout_secs` ≥ 120 on the `read_document` webhook tool.** The 20 s default is
   shorter than a healthy read and will time out every single one. (§3.3G)
4. ⟳ Enable `interruption` under Advanced → Client Events — **and add `agent_chat_response_part`**,
   which is off by default in voice conversations and silently kills captions. (§4.4)
5. `turn_eagerness: "patient"` with a generous `turn_timeout`. (§4.5)
6. Reserved tunnel hostname, with the webhook tool URL pointed at it. (§3.3A)
7. ⟳ Add the explicit failure instruction to the **system prompt text** in
   `agent/persona-prompt.md`, not just its operating-rules prose. (§3.2)

**Code:**

8. `.env.local`: add `http://localhost:4173` to `CORS_ORIGINS` if presenting from `vite preview`. (§1.3)
9. Keep `LLM_TIMEOUT_MS=8000` as the **chat** budget and give `read_document` its own
   `VISION_TIMEOUT_MS=90000`; downscale frames to ≤250 KB before upload. (§3.3G. The old advice here
   was "`LLM_TIMEOUT_MS=12000` for demo day" — that is superseded: 12 s is still below every
   successful Gemma call ever measured, and raising the shared value would have slowed the
   conversational path for no benefit.)
10. ⟳ `frontend/index.html`: `<title>LetterLens</title>`. (§4.2)
11. A `?demo=1` root font-size override rather than restyling everything. (§1.1)
12. A `?mock=1` flag setting `toolMockConfig: { mockingStrategy: "selected", mockedToolNames: ["read_document"] }`. (§3.3I)
13. An "upload a photo instead" input path — product feature and lighting/network fallback in one. (§2.3)
13b. A persistent, large, on-screen **`Reading your letter…`** state that stays up for the whole
    20–57 s call, in the polite live region. It is what makes a long pause legible as work, both to
    the room and to a screen-reader user. (§0.2, §3.1a, §4.1)

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

**Repository** (commit `39b8655`): `agent/persona-prompt.md`, `.env.example`, `.gitignore`,
`frontend/` (`index.html`, `package.json`, `src/App.tsx`, `src/main.tsx`, `src/index.css`,
`src/App.css`, `vite.config.ts`), `backend/requirements.txt`, `test-letters/generate.py` and the
three rendered PNGs, `skills/letter-reader/SKILL.md`, `docs/submission.md`.

Per instruction, **`.env.local` was not read** and no key value appears anywhere in this file.

**Research notes**, all citing primary sources fetched 2026-10-03:
`docs/research/03-elevenlabs-server-tools-and-variables.md` (§§1.3, 1.4, 7, 8, plus the independent
verification pass added in `39b8655`), `docs/research/04-elevenlabs-react-sdk.md` (§§3.4, 6.4, 6.6,
7.1, 7.2, 9.1, 9.2, 9.3, 10), `docs/research/07-gemini-vision-and-structured-output.md` (§§2.4, 2.6),
and `docs/research/08-gemma-live-api-test-results.md` (§§1, 1.1, 1.2, 2, 3, 4, 5, 6, 6.1, 7, 8, 8.1)
— the last of which is **live HTTP against a real key rather than documentation**, and which
supersedes note 01 on the model pin, the image transport and the latency budget. Where this file and
note 01 disagree, note 08 wins; the places that changed are called out inline (§§0.1, 0.2, 2.4,
3.3G, Appendix A item 9).

**Web**, fetched 2026-10-03 — webcam field of view and fixed-focus range:
- [B&H — computer/USB webcam listings](https://www.bhphotovideo.com/c/buy/computer-camera-hd-usb-webcams/ci/6499/pn/5)
- [B&H — JLab GO USB Webcam specifications](https://www.bhphotovideo.com/c/product/1795578-REG/jlab_wgocamrblk124_go_usb_webcam_black.html)
