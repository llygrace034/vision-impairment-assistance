# Structured letter object — field reference

## Status of this document

This schema **mirrors the backend `read_document` tool's return shape**, as
evidenced by the `--- expected extraction ---` blocks at the foot of each file
in `test-letters/`. Those blocks are the only ground truth that exists at the
time of writing; the backend `read_document` implementation is owned by the
human building it.

**The backend implementation is authoritative.** This file does not override it.
If the two diverge, reconcile in favour of the backend and update this file —
do not reshape the backend to match this page, and do not silently accept a
field here that the backend does not return.

Expressibility constraint: this object must survive Gemini-API structured
output, which supports only a subset of JSON Schema and **silently ignores
unsupported properties** (see `docs/research/07-gemini-vision-and-structured-output.md`
§3.4 and §3.6). That is why the object below is shallow, uses
`{"type": ["string", "null"]}` rather than `nullable`, uses `enum` only on
strings, and carries no `$ref`, `oneOf`, `anyOf`, `allOf`, `pattern` or
`additionalProperties` games.

## The object

| Field | Type | Required | Meaning | When the letter does not say |
| --- | --- | --- | --- | --- |
| `doc_type` | string, enum | yes | Routing hint for the kind of letter. Not content, never spoken. | `"other"` |
| `sender` | string | yes | The organisation that sent the letter, as printed. Trust name, council name, school name. Not the signatory. | `"unknown sender"` and `confidence` no higher than `"medium"` |
| `reference` | string or null | yes (may be null) | The reference the sender will ask for on the phone: "Our ref", "PCN number", account or case number. Copied character for character. | `null` |
| `key_dates` | array of DateEntry | yes (may be `[]`) | Every date printed on the letter that the reader could need. Appointment, hearing, departure, payment windows. | `[]` |
| `deadline` | DateEntry or null | yes (may be null) | The single soonest date by which the reader must do something, chosen from `key_dates`. | `null` |
| `actions_required` | array of string | yes (may be `[]`) | What the letter asks the reader to do, one short imperative phrase per action, in the letter's own terms. | `[]` |
| `amounts` | array of Amount | yes (may be `[]`) | Every sum of money printed on the letter. | `[]` |
| `confidence` | string, enum | yes | How well the image was read: `"high"`, `"medium"`, `"low"`. | n/a — always emitted |
| `retry_message` | string or null | yes (may be null) | One short spoken instruction for the user when the read failed, e.g. `"hold the letter closer"`. Non-null **only** when `confidence` is `"low"`. | `null` |

Every field in the table is always present in the object. "Required" means the
key is emitted; several of them may legitimately carry `null` or `[]`.

### DateEntry

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `date` | string | yes | ISO 8601 calendar date, `YYYY-MM-DD`. |
| `time` | string or null | yes (may be null) | 24-hour local time, `HH:MM`. `null` when the letter gives a date with no time. |
| `label` | string | yes | Two to five words saying what the date is for, in the letter's own wording: `"appointment"`, `"discount deadline"`, `"return slip and deposit"`. |

### Amount

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `value` | number | yes | The numeric amount, e.g. `70.0`. No currency symbol, no thousands separator, no string. |
| `currency` | string | yes | ISO 4217 code, e.g. `"GBP"`. A printed `£` is transcribed as `"GBP"`; that is reading the page, not inferring. |
| `label` | string | yes | What the sum is: `"full penalty charge"`, `"reduced if paid early"`, `"deposit"`, `"balance"`. |

## `doc_type` enum

Exactly four values. Three are grounded in the test letters; the fourth is the
fallback.

| Value | Use for | Grounded in |
| --- | --- | --- |
| `hospital_appointment` | Clinic or hospital appointment letters | `test-letters/01-hospital-appointment.txt` |
| `parking_penalty` | Penalty charge notices and parking fines | `test-letters/02-parking-penalty.txt` |
| `school_consent_form` | School letters asking for consent, a signature or a payment | `test-letters/03-school-trip-consent.txt` |
| `other` | Everything else — bills, benefits letters, insurance, marketing, anything unrecognised | fallback |

`other` is not a failure. Most real letters will be `other`, and the rest of
the object carries the content regardless. Never stretch one of the three
specific values to cover a letter it does not describe — a dentist's invoice
is `other`, not `hospital_appointment`.

**Adding a value to this enum is a backend change.** It must be agreed with
whoever owns `read_document` and changed in both places, because the enum is
sent to the model in the response schema.

## Date and time rules

1. `date` is an ISO 8601 calendar date, `YYYY-MM-DD`, zero-padded:
   `2026-11-06`. Never `6/11/26`, never `6 November 2026`, never a
   `YYYY-MM-DDTHH:MM` combined datetime.
2. `time` is a separate field, 24-hour `HH:MM`: `"10:40"`, `"08:15"`,
   `"16:30"`. Never `"10.40am"`.
3. **A date with no time gets `"time": null`.** Not `"00:00"`, not `""`, not
   `"all day"`. A payment deadline has no time; an appointment usually does.
4. No timezone and no offset. These are UK letters and the time printed is the
   local time the reader must turn up at.
5. **The year must be read, not assumed.** If a date is printed without a year,
   take the year from the letter's own printed date line — that is still
   reading the page. If no year can be read anywhere on the page, drop the
   entry and set `confidence` to `"medium"` at best.
6. **Arithmetic on printed values is allowed; invention is not.** Letter 01
   says "at least 5 working days beforehand", which yields a concrete
   `2026-10-30` from the printed appointment date. That entry is legitimate,
   and its `label` must carry the printed wording (`"5 working days before, to
   cancel"`) so the agent can fall back to the wording if challenged.
7. **A relative window with nothing to anchor it is not a date.** Letter 02's
   "informal challenge in writing within 14 days" produces no `key_dates`
   entry; it goes into `actions_required` as `"challenge in writing within 14
   days"`, in the letter's own words.
8. `deadline` is one of the entries already in `key_dates` — the soonest one
   that requires the reader to act. A departure date or a return date is a
   key date, not a deadline. If nothing is required of the reader by any date,
   `deadline` is `null` even when `key_dates` is full.

## Worked example — `test-letters/01-hospital-appointment.txt`

```json
{
  "doc_type": "hospital_appointment",
  "sender": "Mere Valley Hospital Trust",
  "reference": "MVH/OPD/884219",
  "key_dates": [
    { "date": "2026-11-06", "time": "10:40", "label": "appointment" },
    { "date": "2026-10-30", "time": null, "label": "5 working days before, to cancel" }
  ],
  "deadline": {
    "date": "2026-10-30",
    "time": null,
    "label": "5 working days before, to cancel"
  },
  "actions_required": [
    "attend the Dermatology Clinic appointment",
    "or telephone the Booking Centre to cancel",
    "arrive 15 minutes early to check in",
    "bring a list of current medicines"
  ],
  "amounts": [],
  "confidence": "high",
  "retry_message": null
}
```

Points worth noting in that example:

- `amounts` is `[]`, not `"none"`. The fixture's `amounts: none` is prose
  shorthand in a human-readable block; the object uses an empty array.
- The clinician, the referring GP, the recipient's name and address, the
  parking and shuttle paragraph, and the "referred back to your GP" warning
  are all **absent**. They are printed on the page but they are not fields in
  this object, and the object has no free-text field to park them in.
- `reference` is the bare reference, not `"Our ref: MVH/OPD/884219"`.
- `test-letters/03-school-trip-consent.txt` prints no reference number at all.
  That letter's `reference` is `null`. Do not substitute the child's name, the
  class, or anything else that merely looks identifying.

## What must never go into the object

- **Inferred facts.** A weekday worked out from a date. A full name expanded
  from initials. A postcode district turned into a town. A "GBP" guessed from
  context when no currency is printed. If it is not legible on the page, it is
  not a field value.
- **Advice, in any field.** `actions_required` holds what the letter asks for,
  not what the reader should do about it. `"pay GBP 35 by 16 October"` is the
  letter's demand and belongs there. `"you should pay the reduced amount"`,
  `"appeal this"`, `"call your GP about the referral"` are advice and belong
  nowhere.
- **Interpretation of medical, legal or financial content.** No severity, no
  diagnosis gloss, no statement of whether a charge is lawful or a clause
  enforceable.
- **Urgency, tone or sentiment.** No `"urgent"`, no `"important"`, no
  `"threatening"`. If the page prints the word, it can appear inside a `label`
  or an `actions_required` phrase as part of the quoted wording — never as the
  extractor's own judgement.
- **A spoken summary.** The object carries facts; the agent composes the
  sentences. There is no `summary` field and one must not be added here
  without agreeing it with the backend.
- **Padding for absent information.** Never `"none"`, `"unknown"`, `"N/A"`,
  `"not stated"`, `"TBC"` or an empty string as a stand-in. Scalars that are
  absent are `null`; lists that are empty are `[]`. The one exception is
  `sender`, which falls back to the literal `"unknown sender"` so the agent
  always has something to open with.
- **Anything carried over from a previous letter**, a previous turn of the
  conversation, or what the user said they expected to receive.

## Expressible response schema

A direct rendering for `generationConfig.responseFormat.text.schema`, within
the supported subset:

```json
{
  "type": "object",
  "properties": {
    "doc_type": {
      "type": "string",
      "enum": ["hospital_appointment", "parking_penalty", "school_consent_form", "other"]
    },
    "sender": { "type": "string" },
    "reference": { "type": ["string", "null"] },
    "key_dates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "date": { "type": "string", "format": "date" },
          "time": { "type": ["string", "null"] },
          "label": { "type": "string" }
        },
        "required": ["date", "time", "label"]
      }
    },
    "deadline": {
      "type": ["object", "null"],
      "properties": {
        "date": { "type": "string", "format": "date" },
        "time": { "type": ["string", "null"] },
        "label": { "type": "string" }
      },
      "required": ["date", "time", "label"]
    },
    "actions_required": { "type": "array", "items": { "type": "string" } },
    "amounts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "value": { "type": "number" },
          "currency": { "type": "string" },
          "label": { "type": "string" }
        },
        "required": ["value", "currency", "label"]
      }
    },
    "confidence": { "type": "string", "enum": ["high", "medium", "low"] },
    "retry_message": { "type": ["string", "null"] }
  },
  "required": [
    "doc_type", "sender", "reference", "key_dates", "deadline",
    "actions_required", "amounts", "confidence", "retry_message"
  ]
}
```

Two cautions for whoever wires this up, both from
`docs/research/07-gemini-vision-and-structured-output.md`:

- Structured output "guarantees syntactically correct JSON" but not
  semantically correct values (§3.6). Validate the parsed object — dates
  parse, `deadline` appears in `key_dates`, `retry_message` is non-null only
  when `confidence` is `"low"` — before the agent speaks from it.
- `{"type": ["object", "null"]}` on `deadline` is the documented way to allow
  null (§3.4); `nullable` is not in the supported list and unsupported
  properties are silently ignored. If the model still refuses to emit null for
  `deadline`, the fallback is to drop the nesting and carry `deadline_date`
  and `deadline_label` as nullable strings — a backend decision, not one to
  take here.
