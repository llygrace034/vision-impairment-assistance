"""Generate the three synthetic test letters as PNGs.

Everything here is fictional: organisations, people, addresses, reference
numbers and phone numbers do not correspond to real entities. The letters exist
so LetterLens can be demoed and tested without photographing real mail.

The type is deliberately large. These pages get printed on A4 and held up to a
laptop webcam, so nothing on them drops below 16 pt and the key/value panels run
at 22 pt, which keeps the x-height near the ~10 px floor a vision model needs
once the page is scaled down to a webcam frame. Rendering at 300 DPI and
wrapping to the measured text column (rather than a character count) buys back
most of the vertical space the bigger type costs; the rest comes out of the
leading and the panel padding. 18 pt body copy was tried first and ran every
page off the bottom (27-48 mm over), and 17 pt still overran all three, so the
body sits at 16 pt - the bottom-margin check below is what caught both. Do not
raise it again without cutting something. See docs/demo-notes.md for the
arithmetic.

Usage:  python test-letters/generate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent

# A4 at 300 DPI.
DPI = 300
W, H = 2480, 3508
MARGIN = 142          # ~12 mm of white on every edge
COLUMN = W - 2 * MARGIN
LINE = 1.24           # line height, as a multiple of the type size
INK = (26, 26, 26)
PAPER = (253, 252, 249)
ACCENT = (140, 20, 30)


def pt(points: float) -> int:
    """Typographic points -> pixels at the output DPI."""
    return round(points * DPI / 72)


# The type scale. 16 pt is the floor and nothing is allowed under it; the
# key/value panels go larger again because those rows carry the facts the vision
# model absolutely must read.
ORG = pt(28)          # letterhead name
STRAP = pt(16)        # letterhead address line
META = pt(16)         # right-aligned ref / date lines
BODY = pt(16)
SMALL = BODY          # small print on a page read by webcam is not small
LEAD = pt(19)         # salutation
SUBJECT = pt(21)      # "YOUR OUTPATIENT APPOINTMENT ..."
NOTICE = pt(24)       # the one shouty heading on a page
BOX_LABEL = pt(17)
BOX_VALUE = pt(22)

FONT_CANDIDATES = {
    "regular": ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"],
    "bold": ["arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
}
FONT_DIRS = [
    Path("C:/Windows/Fonts"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/truetype/liberation"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
]


def load_font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    for name in FONT_CANDIDATES[weight]:
        for directory in FONT_DIRS:
            candidate = directory / name
            if candidate.exists():
                return ImageFont.truetype(str(candidate), size)
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise RuntimeError(f"no {weight} TrueType font found; install DejaVu or Liberation fonts")


class PageOverflow(RuntimeError):
    """A letter's ink ran past a page margin, so the page would be cropped."""


class Letter:
    """Tiny flowing-text layout engine: draw top to bottom, track the cursor."""

    def __init__(self) -> None:
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self.y = MARGIN
        self.ink_bottom = MARGIN   # lowest pixel row anything has been drawn on
        self.ink_right = MARGIN    # rightmost ditto

    def _claim(self, right: float, bottom: float) -> None:
        """Record the extent of something just drawn, for the margin check."""
        self.ink_right = max(self.ink_right, int(right))
        self.ink_bottom = max(self.ink_bottom, int(bottom))

    def _wrap(self, body, font):
        """Greedy wrap to the measured text column rather than a character count."""
        lines, current = [], ""
        for word in body.split():
            trial = f"{current} {word}".strip()
            if current and self.d.textlength(trial, font=font) > COLUMN:
                lines.append(current)
                current = word
            else:
                current = trial
        lines.append(current)
        return lines

    def text(self, body, size=BODY, weight="regular", gap=20, colour=INK, x=None):
        font = load_font(weight, size)
        left = MARGIN if x is None else x
        for line in self._wrap(body, font):
            self.d.text((left, self.y), line, font=font, fill=colour)
            self._claim(left + self.d.textlength(line, font=font), self.y + size * LINE)
            self.y += int(size * LINE)
        self.y += gap

    def right(self, body, size=META, weight="regular"):
        font = load_font(weight, size)
        width = self.d.textlength(body, font=font)
        self.d.text((W - MARGIN - width, self.y), body, font=font, fill=INK)
        self._claim(W - MARGIN, self.y + size * LINE)
        self.y += int(size * LINE)

    def space(self, px: int = 40) -> None:
        self.y += px

    def rule(self, colour=(200, 198, 192)) -> None:
        self.space(16)
        self.d.line([(MARGIN, self.y), (W - MARGIN, self.y)], fill=colour, width=3)
        self._claim(W - MARGIN, self.y + 3)
        self.space(36)

    def letterhead(self, org, strap, colour=ACCENT):
        self.d.rectangle([(0, 0), (W, 34)], fill=colour)
        self.y = MARGIN
        self.text(org, size=ORG, weight="bold", gap=8, colour=colour)
        self.text(strap, size=STRAP, gap=8, colour=(70, 70, 70))
        self.rule()

    def box(self, rows, value_size=BOX_VALUE, pad=30):
        """A bordered key/value panel - the kind of block the vision model must get right.

        Labels are full-strength ink, not grey: these are the words "Date",
        "Time" and "Pay reduced amount by", and they are the first thing to
        dissolve under a webcam in poor light.
        """
        label_font = load_font("regular", BOX_LABEL)
        value_font = load_font("bold", value_size)
        row_h = int(value_size * 1.15)
        height = pad * 2 + row_h * len(rows)
        top = self.y
        self.d.rectangle([(MARGIN, top), (W - MARGIN, top + height)],
                         outline=(170, 168, 162), width=3, fill=(246, 245, 241))
        gutter = max(self.d.textlength(label, font=label_font) for label, _ in rows) + pad
        for i, (label, value) in enumerate(rows):
            ry = top + pad + i * row_h
            self.d.text((MARGIN + pad, ry + (value_size - BOX_LABEL) // 2), label,
                        font=label_font, fill=INK)
            self.d.text((MARGIN + pad + gutter, ry), value, font=value_font, fill=INK)
            self._claim(MARGIN + pad + gutter + self.d.textlength(value, font=value_font),
                        ry + value_size * LINE)
        self._claim(W - MARGIN, top + height)
        self.y = top + height + 40

    def check(self, stem: str) -> None:
        """Fail loudly if the page would be cropped. Called before anything is written."""
        faults = []
        if self.ink_bottom > H - MARGIN:
            over = self.ink_bottom - (H - MARGIN)
            faults.append(
                f"content runs {over} px ({over / DPI * 25.4:.1f} mm) past the bottom "
                f"margin - ink ends at y={self.ink_bottom}, the margin starts at y={H - MARGIN}"
            )
        if self.ink_right > W - MARGIN:
            over = self.ink_right - (W - MARGIN)
            faults.append(
                f"a line runs {over} px past the right margin - ink reaches "
                f"x={self.ink_right}, the margin starts at x={W - MARGIN}"
            )
        if faults:
            raise PageOverflow(
                f"{stem}: " + "; and ".join(faults)
                + ". No PNG was written. Step a type size down or tighten the spacing - "
                  "do not crop the page and do not drop content."
            )

    def save(self, stem: str, source_text: str) -> None:
        self.check(stem)
        png = HERE / f"{stem}.png"
        txt = HERE / f"{stem}.txt"
        self.img.save(png, "PNG", optimize=True)
        txt.write_text(source_text.strip() + "\n", encoding="utf-8")
        slack = (H - MARGIN) - self.ink_bottom
        print(f"wrote {png.name} ({png.stat().st_size // 1024} KB) and {txt.name}"
              f" - {slack} px ({slack / DPI * 25.4:.0f} mm) of bottom margin to spare")


def hospital_appointment() -> None:
    L = Letter()
    L.letterhead("Mere Valley Hospital Trust",
                 "Outpatient Booking Centre - Northgate Site - Mereford MF4 2QL",
                 colour=(10, 70, 140))
    L.right("Our ref: MVH/OPD/884219")
    L.right("Date: 14 October 2026")
    L.space(28)
    L.text("Mrs Eleanor Whitcombe", weight="bold", gap=4)
    L.text("12 Alderwood Close", gap=4)
    L.text("Mereford MF2 7BH", gap=26)
    L.space(14)
    L.text("Dear Mrs Whitcombe", size=LEAD, weight="bold", gap=20)
    L.text("YOUR OUTPATIENT APPOINTMENT - DERMATOLOGY", size=SUBJECT, weight="bold", gap=22)
    L.text(
        "You have been given an appointment in the Dermatology Clinic following "
        "the referral from your GP, Dr Haleema Sunderland, at Alderwood Surgery."
    )
    L.box([
        ("Clinic", "Dermatology (Clinic 4B)"),
        ("Date", "Thursday 6 November 2026"),
        ("Time", "10:40"),
        ("Location", "Northgate Site, Level 2"),
        ("Clinician", "Dr A. Oyelaran"),
    ])
    L.text(
        "Please arrive 15 minutes before your appointment time to book in at the "
        "self-check-in screens in the main atrium. Bring a list of any medicines "
        "you are currently taking, and your reading glasses if you use them."
    )
    L.text(
        "If you cannot attend, please telephone the Booking Centre on 01xx 496 7730 "
        "at least 5 working days beforehand so the slot can be offered to someone "
        "else. If you miss two appointments without telling us, you may be referred "
        "back to your GP."
    )
    L.text(
        "Parking at the Northgate Site is limited. Blue badge spaces are available "
        "in Car Park C, and the hospital shuttle runs from the Mereford Park and "
        "Ride every 20 minutes."
    )
    L.space(16)
    L.text("Yours sincerely", gap=60)
    L.text("J. Pemberton-Hale", weight="bold", gap=4)
    L.text("Outpatient Booking Manager", size=SMALL, gap=4)
    L.save("01-hospital-appointment", """
Mere Valley Hospital Trust - Outpatient Booking Centre
Our ref: MVH/OPD/884219 - Date: 14 October 2026

Mrs Eleanor Whitcombe, 12 Alderwood Close, Mereford MF2 7BH

YOUR OUTPATIENT APPOINTMENT - DERMATOLOGY

You have been given an appointment in the Dermatology Clinic following the
referral from your GP, Dr Haleema Sunderland, at Alderwood Surgery.

Clinic:     Dermatology (Clinic 4B)
Date:       Thursday 6 November 2026
Time:       10:40
Location:   Northgate Site, Level 2
Clinician:  Dr A. Oyelaran

Please arrive 15 minutes before your appointment time to book in at the
self-check-in screens in the main atrium. Bring a list of any medicines you are
currently taking, and your reading glasses if you use them.

If you cannot attend, please telephone the Booking Centre on 01xx 496 7730 at
least 5 working days beforehand. If you miss two appointments without telling
us, you may be referred back to your GP.

Parking at the Northgate Site is limited. Blue badge spaces are available in Car
Park C, and the hospital shuttle runs from the Mereford Park and Ride every 20
minutes.

Yours sincerely
J. Pemberton-Hale, Outpatient Booking Manager

--- expected extraction ---
doc_type: hospital_appointment
sender: Mere Valley Hospital Trust
key_dates: 2026-11-06 10:40 (appointment)
deadline: 2026-10-30 (5 working days before, to cancel)
actions_required: attend or call to cancel; bring medicines list
amounts: none
""")


def parking_penalty() -> None:
    L = Letter()
    L.letterhead("Borough of Kerneby",
                 "Civil Parking Enforcement - PO Box 1184 - Kerneby KB1 9XY")
    L.right("PCN number: KB7719240385")
    L.right("Date of issue: 2 October 2026")
    L.space(28)
    L.text("Mr Dominic Abara", weight="bold", gap=4)
    L.text("Flat 6, Saltmarsh House", gap=4)
    L.text("Kerneby KB3 4RD", gap=26)
    L.space(14)
    L.text("PENALTY CHARGE NOTICE", size=NOTICE, weight="bold", colour=ACCENT, gap=16)
    L.text(
        "Issued under the Traffic Management Act 2004 in respect of the vehicle "
        "described below, which was observed by a civil enforcement officer."
    )
    L.box([
        ("Vehicle", "KB19 ZTC (grey hatchback)"),
        ("Location", "Harbour Row, bay 12"),
        ("Date & time", "28 September 2026, 14:52"),
        ("Contravention", "01 - restricted street"),
    ])
    L.text("AMOUNT TO PAY", size=SUBJECT, weight="bold", gap=16)
    L.box([
        ("Full penalty charge", "GBP 70.00"),
        ("Reduced if paid early", "GBP 35.00"),
        ("Pay reduced amount by", "16 October 2026"),
        ("Pay full amount by", "30 October 2026"),
    ])
    L.text(
        "If the reduced amount of 35 pounds is not received by 16 October 2026 the "
        "full charge of 70 pounds becomes payable. If no payment or representation "
        "is received by 30 October 2026 a Notice to Owner may be served and the "
        "charge may increase by a further 50 percent.",
        size=SMALL, gap=16,
    )
    L.text(
        "Pay online at the Borough payments portal quoting the PCN number above, or "
        "by telephone on 01xx 220 4411 (automated, 24 hours).",
        size=SMALL, gap=16,
    )
    L.text(
        "If you believe this notice was issued incorrectly you may make an informal "
        "challenge in writing within 14 days. Making a challenge does not extend "
        "the discount period unless the challenge is accepted.",
        size=SMALL, gap=16,
    )
    L.space(14)
    L.text("Parking Services, Borough of Kerneby", size=SMALL, colour=(70, 70, 70))
    L.save("02-parking-penalty", """
Borough of Kerneby - Civil Parking Enforcement
PCN number: KB7719240385 - Date of issue: 2 October 2026

Mr Dominic Abara, Flat 6, Saltmarsh House, Kerneby KB3 4RD

PENALTY CHARGE NOTICE
Issued under the Traffic Management Act 2004.

Vehicle:        KB19 ZTC (grey hatchback)
Location:       Harbour Row, bay 12
Date & time:    28 September 2026, 14:52
Contravention:  01 - parked in a restricted street during prescribed hours

AMOUNT TO PAY
Full penalty charge:      GBP 70.00
Reduced if paid early:    GBP 35.00
Pay reduced amount by:    16 October 2026
Pay full amount by:       30 October 2026

If the reduced amount of GBP 35 is not received by 16 October 2026 the full
charge of GBP 70 becomes payable. If no payment or representation is received by
30 October 2026 a Notice to Owner may be served and the charge may increase by a
further 50 percent.

Pay online at the Borough payments portal quoting the PCN number, or by
telephone on 01xx 220 4411 (automated, 24 hours).

If you believe this notice was issued incorrectly you may make an informal
challenge in writing within 14 days. Making a challenge does not extend the
discount period unless the challenge is accepted.

Parking Services, Borough of Kerneby

--- expected extraction ---
doc_type: parking_penalty
sender: Borough of Kerneby
amounts: GBP 70.00 (full), GBP 35.00 (reduced)
key_dates: 2026-10-16 (discount deadline), 2026-10-30 (full payment deadline)
deadline: 2026-10-16
actions_required: pay GBP 35 by 16 Oct, or challenge within 14 days
""")


def school_trip_consent() -> None:
    L = Letter()
    L.letterhead("Thornfield Lane Primary School",
                 "Thornfield Lane - Westhampstead WH8 3LT - Head: Mr R. Castellane",
                 colour=(20, 95, 70))
    L.right("Date: 5 October 2026")
    L.space(28)
    L.text("Dear Parent or Guardian of Amara Nkemelu (Class 5B),", size=LEAD,
           weight="bold", gap=22)
    L.text("YEAR 5 RESIDENTIAL TRIP - CARRICK BAY FIELD CENTRE", size=SUBJECT,
           weight="bold", gap=22)
    L.text(
        "Year 5 will visit the Carrick Bay Field Centre for three days of coastal "
        "geography and team activities. The programme includes rock pooling, a "
        "cliff-top walk and an evening orienteering exercise."
    )
    L.box([
        ("Departure", "Mon 17 November 2026, 08:15"),
        ("Return", "Wed 19 November 2026, 16:30"),
        ("Meeting point", "School main gate"),
        ("Total cost", "GBP 148.00 per pupil"),
        ("Deposit", "GBP 40.00"),
    ])
    L.text("PLEASE RETURN BY FRIDAY 24 OCTOBER 2026", size=SUBJECT, weight="bold",
           colour=ACCENT, gap=22)
    L.text(
        "To confirm your child's place we need the signed consent slip below and "
        "the deposit of 40 pounds by Friday 24 October 2026. The balance of 108 "
        "pounds is due by Friday 7 November 2026. Payment is through the school's "
        "online payment system; if you would prefer to pay in instalments please "
        "speak to the school office in confidence."
    )
    L.text(
        "Please also tell us about any medication, dietary requirement or medical "
        "condition we should know about, even if it is already on your child's "
        "school record."
    )
    L.rule()
    L.text("CONSENT SLIP - please detach and return", weight="bold", gap=20)
    L.text("I give permission for my child to attend the Carrick Bay residential trip.",
           size=SMALL, gap=26)
    L.text("Child's name: ______________________   Class: __________", size=SMALL, gap=22)
    L.text("Medication / dietary needs: _________________________________", size=SMALL, gap=22)
    L.text("Emergency contact number: __________________________________", size=SMALL, gap=22)
    L.text("Signed: ______________________   Date: ______________", size=SMALL, gap=8)
    L.save("03-school-trip-consent", """
Thornfield Lane Primary School
Date: 5 October 2026

Dear Parent or Guardian of Amara Nkemelu (Class 5B),

YEAR 5 RESIDENTIAL TRIP - CARRICK BAY FIELD CENTRE

Year 5 will visit the Carrick Bay Field Centre for three days of coastal
geography and team activities. The programme includes rock pooling, a cliff-top
walk and an evening orienteering exercise.

Departure:      Monday 17 November 2026, 08:15
Return:         Wednesday 19 November 2026, 16:30
Meeting point:  School main gate
Total cost:     GBP 148.00 per pupil
Deposit:        GBP 40.00

PLEASE RETURN BY FRIDAY 24 OCTOBER 2026

To confirm your child's place we need the signed consent slip and the deposit of
GBP 40 by Friday 24 October 2026. The balance of GBP 108 is due by Friday 7
November 2026. Payment is through the school's online payment system; if you
would prefer to pay in instalments please speak to the school office in
confidence.

Please also tell us about any medication, dietary requirement or medical
condition we should know about.

CONSENT SLIP - please detach and return
I give permission for my child to attend the Carrick Bay residential trip.
Child's name: ______ Class: ______
Medication / dietary needs: ______
Emergency contact number: ______
Signed: ______ Date: ______

--- expected extraction ---
doc_type: school_consent_form
sender: Thornfield Lane Primary School
amounts: GBP 148.00 (total), GBP 40.00 (deposit), GBP 108.00 (balance)
key_dates: 2026-11-17 08:15 (departure), 2026-11-19 16:30 (return),
           2026-10-24 (return slip + deposit), 2026-11-07 (balance due)
deadline: 2026-10-24
actions_required: sign and return consent slip, pay GBP 40 deposit,
                  declare medication/dietary needs
""")


if __name__ == "__main__":
    try:
        hospital_appointment()
        parking_penalty()
        school_trip_consent()
    except PageOverflow as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
