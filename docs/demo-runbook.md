# LetterLens — demo runbook

Grounded in `backend/app.py` and `frontend/src/App.tsx` at the current working tree. Everything
below is in the code today. Print this.

---

## 1. Pre-flight (60 seconds)

**Terminal 1 — backend** (from repo root `C:\Users\arun\vision-impairment-assistance`):

```
./.venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Wait for `Uvicorn running on http://127.0.0.1:8000`.

**Terminal 2 — frontend** (from `frontend/`):

```
npm run dev
```

Wait for `Local: http://localhost:5173/`. Use **localhost**, not the LAN IP — `CORS_ORIGINS`
allows `http://localhost:5173` and `http://127.0.0.1:5173` only, and a plain IP is not a secure
context for the camera.

**Health check** (Terminal 3, or a browser tab):

```
curl http://127.0.0.1:8000/health
```

Expected shape — all three key fields must be truthy:

```json
{"ok":true,"gemini_key":true,"elevenlabs_key":true,"agent_id":"<agent id string>","vision_model":"gemma-4-26b-a4b-it"}
```

`gemini_key:false` → vision will 500. `elevenlabs_key:false` or `agent_id:null` → `/signed-url`
will 500 and the Start button fails. Both are read at import, so **fix `.env.local` then restart
the backend.**

**Optional vision smoke test** (proves the Gemma path without spending any TTS quota):

```
curl -s -F "image=@test-letters/01-hospital-appointment.png" http://127.0.0.1:8000/read_document
```

Returns `{"text": "FROM: ... REF: ...", "elapsed_s": 4.x}`.

**Last 10 seconds:** open `http://localhost:5173`, confirm the camera preview is live and the
status line reads `Not connected`. Have `test-letters/01-hospital-appointment.png` open full-screen
on a phone, brightness up. Have `02-parking-penalty.png` and `03-school-trip-consent.png` ready to
swipe to.

---

## 2. Happy path

1. **Page loads.** Camera preview appears immediately — the camera starts on mount, before any
   connection, so you can frame the letter first. Status: `Not connected`.
2. **Hold the letter to the webcam.** Fill the frame, flat, no glare. Do this *before* clicking
   Start so there is no dead air later.
3. **Click "Start talking."** The browser asks for the **microphone** at this point (camera was
   already granted on load). Allow it. Status goes `Connecting…` → `Listening — hold up a letter
   and ask what it says`.
4. **Say:** *"Can you read this letter for me?"*
5. The agent calls the `read_document` client tool. The badge **`Reading…`** appears over the
   preview and the status line changes to `Reading the letter…`.
6. **This is the gap: ~5–8 seconds.** Measured on the wire: 4.6 s (hospital letter), 7.8 s
   (parking penalty), 8.3 s (school trip consent). **Narrate it — do not stand in silence.** Say
   something like: *"It has just grabbed a frame off the webcam, scaled it down, and it is doing a
   single vision pass on it now — that is the whole round trip you are waiting on."* Stop talking
   before the agent does.
7. **The agent speaks a summary** of who the letter is from, what it is about, the date and time,
   any deadline or amount, the reference number and a contact number — in its own words, not a
   verbatim read-out. The backend asks the model for at most six labelled lines and copies dates,
   amounts and reference numbers exactly as printed; the agent summarises from that.
8. **The "Last read" panel** appears underneath with the raw extracted text. Point at it: this is
   what the model actually returned, so the room can check the agent against it.
9. **Follow up by voice** — *"What was the reference number?"*, *"When is it?"* — the agent already
   has the text and answers with **no second tool call and no wait.** This is the strongest beat in
   the demo; use it.
10. **Swipe to letter 2**, hold it up, *"Read this one."* Repeat once, not twice.
11. **Click "Stop"** to end the session. Do this before you start talking to the room — it stops
    the mic and stops burning TTS quota.

**Quota warning:** the ElevenLabs account is on the **free tier, 10,000 TTS characters/month.**
Every spoken reply and every rehearsal spends it. Do **not** rehearse the voice path more than once
before going live, and hit Stop whenever you are not actively demoing.

---

## 3. Failure playbook

| Symptom | Likely cause | 10-second fix |
|---|---|---|
| Red error line `Camera unavailable: …`, no preview | Camera permission denied or another app holds the webcam | Padlock in the address bar → allow Camera → **reload the page** (the camera is only requested on mount). Close Zoom/Teams/OBS. |
| Click Start, red error line, status stays `Not connected` | Mic permission denied | Padlock → allow Microphone → **click Start again** (no reload needed; the mic is requested on every Start). |
| Click Start, error mentions `Failed to fetch` or `token request failed` | Backend not running or crashed | Check Terminal 1; re-run the uvicorn command; `curl http://127.0.0.1:8000/health`. |
| Error `token request failed (502)` | ElevenLabs rejected the token mint (401/403 — bad, revoked or wrong-workspace key). Backend log shows the real status. | `/health` → if `elevenlabs_key:false`, the key is not loaded. Fix `.env.local`, **restart the backend** (env is read at import). |
| Agent says *"I could not read that in time. Please hold the letter still and try again."* | Gemma call exceeded the 25 s vision timeout | Flatten the letter, more light, kill glare, ask again. Nothing to restart — the backend handled it and stayed up. |
| Agent says *"I cannot quite make that out. Hold the letter a little closer and flatten it for me."* | Model returned `UNREADABLE` — blurry, dark or cut off | Move the phone/paper closer, raise screen brightness, re-ask. |
| Agent says *"I had trouble reading that"* / *"I could not reach the reader"* | Non-200 from Gemini (bad/quota'd `GEMINI_API_KEY`), or the browser could not reach the backend at all | Check the backend terminal for the status code; `curl /health` for `gemini_key:true`. If the fetch itself failed, it is CORS or the wrong origin — use `localhost:5173`. |
| Connects, status `Listening`, you ask — nothing happens, no `Reading…` badge | The agent never invoked the tool: tool not registered on the agent, or named something other than `read_document` | Re-ask explicitly: *"Use the document reader to read this letter."* If still nothing, the agent config is wrong — switch to the curl fallback below; do not debug the dashboard live. |
| Connects but the agent is silent / session drops instantly | Free-tier TTS quota exhausted | Not fixable in the room. **Fall back:** show the curl against `test-letters/` on screen — it demonstrates the full vision path and the exact text the agent would have spoken. |

**Universal 10-second reset:** click Stop, reload the page, click Start talking. Every error in the
UI surfaces in the single red line under the button (`role="alert"`) — read it out of that line
rather than guessing.

---

## 4. If asked about the architecture

`read_document` is an ElevenLabs **client tool**, not a webhook/server tool. The browser already
holds the camera frame, so when the agent calls the tool, the handler in `App.tsx` grabs the current
frame, downscales it to 1024 px wide JPEG at quality 0.75, POSTs it to our own FastAPI backend as
multipart field `image`, the backend does one Gemma vision pass, and the handler returns that text
straight back to the agent as a string, which the agent then summarises aloud. The alternative — a
server tool — means ElevenLabs calls our backend from their cloud, and the backend has to correlate
*that* inbound call with a frame the browser uploaded separately. Making the tool run in the
browser deletes that correlation problem, and with it three moving parts: **no ngrok tunnel, no
`PUBLIC_BASE_URL`, and no `TOOL_WEBHOOK_SECRET`.** The backend keeps exactly two jobs — mint a
short-lived conversation token so the browser never sees `ELEVENLABS_API_KEY`, and run the vision
pass — and the only public surface is localhost. Two other deliberate choices: the backend returns
**plain labelled text, not JSON**, because the agent is the thing that summarises and a strict
response schema was not honoured by the model; and failures are returned to the agent as a *sentence
it can say out loud* rather than raised as a 5xx, because an error throw makes the agent apologise
vaguely with no idea what went wrong.
