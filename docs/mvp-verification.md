# MVP verification log — 2026-10-03

Live end-to-end run of `backend/app.py` against the real Gemini API
(`gemma-4-26b-a4b-it`) and the real ElevenLabs token endpoint. Measured on
Windows 11, Python 3.11 in `.venv`, three test letters from `test-letters/`.

## Verdict

**Yes — the MVP works end to end.** All six endpoint behaviours pass: keys load,
a conversation token mints, all three letters return readable prose in 4.4–8.5s,
and both failure paths come back as speakable sentences or a clean 400 rather
than a 5xx.

Two content gaps, both reproducible across three runs, both in the vision layer
rather than the plumbing:

1. Letter 01 (hospital) returns `DEADLINE: NONE` — it drops the "5 working days
   before" cancellation notice period.
2. Letter 03 (school trip) returns **no amounts at all** — GBP 148.00 total,
   GBP 40.00 deposit and GBP 108.00 balance are all missing. For a letter whose
   whole point is "pay GBP 40 by 24 October", that is the most important fact.

Nothing a demo cannot survive, but letter 03's missing money is a real accuracy
defect and is recorded as a FAIL below, not a pass.

## Working start command

```powershell
cd C:\Users\arun\vision-impairment-assistance
.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000
```

`backend.app:app` imports cleanly from the repo root. **The current working
directory must be the repo root** — `load_dotenv(".env.local")` in `app.py` is a
relative path, so from anywhere else every key loads empty.

Proven, not assumed. Two instances started from the same interpreter:

| Started from | Command | `gemini_key` | `elevenlabs_key` | `agent_id` |
|---|---|---|---|---|
| repo root | `uvicorn backend.app:app --port 8010` | `true` | `true` | present |
| `C:\Users\arun` | `uvicorn backend.app:app --port 8011 --app-dir <repo>` | **`false`** | **`false`** | `null` |

`--app-dir` fixes the *import* and the server starts and answers `/health` with
`"ok": true` — it does **not** fix `load_dotenv`. There is no visible error; the
first `/read_document` would just 500 with "GEMINI_API_KEY is not set".

Also note `/health`'s `vision_model` field reads `gemma-4-26b-a4b-it` in **both**
rows above, because that string is the hardcoded default in `app.py`. It is not
evidence that `.env.local` loaded. Only `gemini_key` and `elevenlabs_key` are.

## Endpoint results

`GET /health` → 200 in 0.03s, `gemini_key: true`, `elevenlabs_key: true`,
`vision_model: gemma-4-26b-a4b-it`, agent id present.

`GET /signed-url` → 200 in 2.69s. Token returned: 1039 characters, prefix
`eyJhbGciOiJI` (a JWT). Value not recorded anywhere.

## Per-letter accuracy

Frames were prepared exactly as the browser prepares them: 2480×3508 PNG
downscaled to 1024×1448, JPEG quality 0.75, ~200 KB, posted as multipart with
field name `image`. Three runs each.

Latency (backend-reported `elapsed_s`; wall clock was within 0.05s every time):

| Letter | run 1 | run 2 | run 3 | best | worst |
|---|---|---|---|---|---|
| 01 hospital appointment | 8.12s | 4.39s | 4.64s | 4.39s | 8.12s |
| 02 parking penalty | 8.53s | 5.19s | 5.12s | 5.12s | 8.53s |
| 03 school trip consent | 5.09s | 5.36s | 5.33s | 5.09s | 5.36s |

All nine calls HTTP 200. Range across all nine: **4.39s – 8.53s**, median ~5.2s.
The two 8s outliers were both first-of-session calls; nothing approached the 60s
cap.

### 01 — hospital appointment: PASS with one omission

Returned (run 3):

```
FROM: Mere Valley Hospital Trust
ABOUT: Your outpatient appointment in Dermatology
WHEN: 14 October 2026; Thursday 6 November 2026, 10:40
DEADLINE: NONE
REF: MVH/OPD/884219
CONTACT: 01xx 496 7730
```

| Field | Ground truth | Returned | Verdict |
|---|---|---|---|
| Sender | Mere Valley Hospital Trust | Mere Valley Hospital Trust | PASS |
| Appointment date/time | Thursday 6 November 2026, 10:40 | Thursday 6 November 2026, 10:40 | PASS |
| Reference | MVH/OPD/884219 | MVH/OPD/884219 | PASS — exact, digit for digit |
| Deadline | cancel ≥5 working days before (≈30 Oct 2026) | NONE | **FAIL** |
| Phone | 01xx 496 7730 | 01xx 496 7730 | PASS |

The critical field — the appointment time — is exact in all three runs. `WHEN`
also carries the letter's own issue date (14 October 2026) ahead of the
appointment date; harmless but the agent must not read the first date as the
appointment. The deadline miss is reproducible 3/3.

### 02 — parking penalty: PASS, all fields exact

Returned (run 1, identical in substance across all three runs):

```
FROM: Borough of Kerneby
ABOUT: Penalty charge notice for restricted street contravention
WHEN: 2 October 2026; 28 September 2026, 14:52
DEADLINE: GBP 35.00 by 16 October 2026; GBP 70.00 by 30 October 2026
REF: KB7719240385
CONTACT: 01xx 220 4411
```

| Field | Ground truth | Returned | Verdict |
|---|---|---|---|
| Sender | Borough of Kerneby | Borough of Kerneby | PASS |
| Contravention date/time | 28 September 2026, 14:52 | 28 September 2026, 14:52 | PASS |
| Amount — reduced | GBP 35.00 by 16 October 2026 | GBP 35.00 by 16 October 2026 | PASS |
| Amount — full | GBP 70.00 by 30 October 2026 | GBP 70.00 by 30 October 2026 | PASS |
| PCN number | KB7719240385 | KB7719240385 | PASS — exact, 12 characters |
| Phone | 01xx 220 4411 | 01xx 220 4411 | PASS |

Best of the three. Both amounts, both deadlines and the full PCN correct every run.

### 03 — school trip consent: FAIL on amounts

Returned (run 3):

```
FROM: Thornfield Lane Primary School
ABOUT: Year 5 residential trip to Carrick Bay Field Centre
WHEN: 5 October 2026, Mon 17 November 2026, 08:15, Wed 19 November 2026, 16:30
DEADLINE: Friday 24 October 2026 (deposit), Friday 7 November 2026 (balance)
REF: NONE
CONTACT: NONE
```

| Field | Ground truth | Returned | Verdict |
|---|---|---|---|
| Sender | Thornfield Lane Primary School | Thornfield Lane Primary School | PASS |
| Departure | Mon 17 November 2026, 08:15 | Mon 17 November 2026, 08:15 | PASS |
| Return | Wed 19 November 2026, 16:30 | Wed 19 November 2026, 16:30 | PASS |
| Deadline — slip + deposit | Friday 24 October 2026 | Friday 24 October 2026 | PASS |
| Deadline — balance | Friday 7 November 2026 | Friday 7 November 2026 | PASS |
| Amounts | GBP 148.00 total / 40.00 deposit / 108.00 balance | **absent** | **FAIL** |
| Reference | none printed | NONE | PASS (correctly absent) |
| Phone | none printed | NONE | PASS (correctly absent) |

Reproducible 3/3: the model fills `DEADLINE` with dates and drops the money,
even though the prompt asks for "any deadline **or amount due**". Run 1 was
worse still — it omitted the 08:15 and 16:30 times as well; runs 2 and 3 had
them. So the dates are not fully stable either.

## Error paths

| Case | Input | Result |
|---|---|---|
| Unreadable — solid black | 1024×1448 black JPEG | HTTP **200** in 3.24s, `"I cannot quite make that out. Hold the letter a little closer and flatten it for me."` |
| Unreadable — heavy blur | letter 01 at 1024px, Gaussian blur radius 18 | HTTP **200** in 5.22s, same retry sentence |
| Empty upload | zero-byte file part named `image` | HTTP **400**, `{"detail":"empty image upload"}` |
| Missing field | file part named something other than `image` | HTTP **422**, FastAPI validation body |

Both unreadable cases behave as designed: Gemma emits `UNREADABLE`, the backend
converts it to a speakable retry sentence and still reports `elapsed_s`. No 5xx
on any error path. Test images were written to the session temp directory, not
the repo.

## Still broken / open

1. **Letter 03 returns no amounts.** Reproducible 3/3. Prompt-level fix: give
   `AMOUNT` its own line instead of sharing `DEADLINE`. Requires an edit to
   `READ_PROMPT` in `backend/app.py`, which this lane did not own.
2. **Letter 01 returns `DEADLINE: NONE`** for the 5-working-day cancellation
   notice. Lower stakes than (1), same root cause.
3. **`WHEN` mixes the letter's own issue date with the event date**, issue date
   first on letters 01 and 02. The agent's persona needs to not read the first
   date it hears as "your appointment".
4. **`/health` cannot distinguish a loaded `GEMMA_VISION_MODEL` from the
   hardcoded default**, so it reports the right model name even when nothing
   loaded. `gemini_key`/`elevenlabs_key` are the only trustworthy fields.
5. **No regression test covers this.** The accuracy above was measured by hand;
   nothing in the repo would catch letter 03's amounts regressing further.
6. Output is six labelled lines, not the structured object in
   `skills/letter-reader/references/output-schema.md`. Known and intended, noted
   here only so the discrepancy is on the record.

## Method notes

- Interpreter: `C:\Users\arun\vision-impairment-assistance\.venv\Scripts\python.exe`
- Ports 8010 and 8011 were used so as not to disturb a server already listening
  on 8000. Both were killed afterwards; ports confirmed free.
- No secret value appears in this file. The signed-url token is recorded only by
  length and first 12 characters.
