"""Camera-realism harness for LetterLens.

Renders a small paper document from a simple spec, degrades it the way a laptop
webcam or phone camera would (tilt, rotation, blur, uneven light, sensor noise,
background clutter), downsizes it exactly as frontend/src/App.tsx does
(1024px wide, JPEG quality 0.75) and posts it to the running backend.

Library use (from any Python script run with the repo venv, from the repo root):

    from scripts.camera_sim import render, degrade, post, run_case
    lines = [("h", "PHARMACY RECEIPT"), ("m", "Paracetamol 500mg x16   GBP 1.20")]
    img = render(lines, size_mm=(80, 120))
    frame = degrade(img, profile="typical", seed=3)
    result = post(frame)              # -> dict with 'text', 'elapsed_s'
    # or in one go, saving the frame + result under scripts/camera_sim_out/<name>:
    result = run_case("pharmacy-receipt", lines, size_mm=(80, 120), profile="typical")

Spec lines are (style, text) tuples. Styles:
    "h"   big bold heading        "h2"  medium bold
    "p"   body text               "s"   small print
    "m"   monospace (receipts)    "hw"  handwriting-style (Segoe Print / Comic)
    "hwb" big handwriting         "gap" blank line (text ignored)
    "kv"  "Label: value" bold label   "rule" horizontal rule
Any style may be suffixed with "-c" to centre or "-r" to right-align, e.g. "h-c".

Profiles: "good" (phone, steady, well lit), "typical" (laptop webcam, slight
tilt), "poor" (dim, blurry, more tilt). All three stay within what a human would
still consider readable; "poor" is the edge of that.

Run directly for a smoke test of a sticky note through all three profiles.
"""

from __future__ import annotations

import io
import json
import random
import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "scripts" / "camera_sim_out"
BACKEND = "http://127.0.0.1:8000"

DPI = 200  # render DPI for the paper itself; the frame is downsized afterwards
INK = (28, 28, 30)
PAPER = (251, 250, 246)

FONT_DIR = Path("C:/Windows/Fonts")
FONTS = {
    "regular": ["arial.ttf", "DejaVuSans.ttf"],
    "bold": ["arialbd.ttf", "DejaVuSans-Bold.ttf"],
    "mono": ["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"],
    "hand": ["segoepr.ttf", "segoesc.ttf", "comic.ttf", "arial.ttf"],
}


def _font(kind: str, size_pt: float) -> ImageFont.FreeTypeFont:
    px = max(8, round(size_pt * DPI / 72))
    for name in FONTS[kind]:
        p = FONT_DIR / name
        if p.exists():
            return ImageFont.truetype(str(p), px)
    return ImageFont.load_default()


STYLE = {
    # style: (font kind, point size, line-height multiple)
    "h": ("bold", 20, 1.3),
    "h2": ("bold", 14, 1.3),
    "p": ("regular", 11, 1.3),
    "s": ("regular", 8.5, 1.25),
    "m": ("mono", 10, 1.25),
    "hw": ("hand", 14, 1.35),
    "hwb": ("hand", 22, 1.35),
    "kv": ("regular", 11, 1.3),
    "gap": ("regular", 11, 0.7),
    "rule": ("regular", 11, 0.8),
}


def _mm(mm: float) -> int:
    return round(mm / 25.4 * DPI)


def render(lines, size_mm=(100, 140), margin_mm=7, ink=INK, paper=PAPER) -> Image.Image:
    """Render spec lines onto a paper of the given physical size (w, h) in mm.

    Text wraps to the column. If the content overflows the paper the paper is
    extended downward, so nothing is silently lost; check the returned size.
    """
    w = _mm(size_mm[0])
    h = _mm(size_mm[1])
    margin = _mm(margin_mm)
    column = w - 2 * margin
    img = Image.new("RGB", (w, h), paper)
    draw = ImageDraw.Draw(img)
    y = margin

    for style, text in lines:
        align = "l"
        if style.endswith("-c"):
            align, style = "c", style[:-2]
        elif style.endswith("-r"):
            align, style = "r", style[:-2]
        kind, size, lh = STYLE[style]
        font = _font(kind, size)
        line_px = round(size * DPI / 72 * lh)

        if style == "gap":
            y += line_px
            continue
        if style == "rule":
            draw.line([(margin, y + line_px // 2), (w - margin, y + line_px // 2)], fill=ink, width=2)
            y += line_px
            continue

        if style == "kv" and ":" in text:
            label, value = text.split(":", 1)
            bold = _font("bold", size)
            lw = draw.textlength(label + ":", font=bold)
            if y + line_px > h - margin:
                img, draw, h = _extend(img, line_px * 3)
            draw.text((margin, y), label + ":", font=bold, fill=ink)
            draw.text((margin + lw + _mm(2), y), value.strip(), font=font, fill=ink)
            y += line_px
            continue

        for wrapped in _wrap(draw, text, font, column):
            if y + line_px > h - margin:
                img, draw, h = _extend(img, line_px * 3)
            tw = draw.textlength(wrapped, font=font)
            x = margin if align == "l" else (w - tw) / 2 if align == "c" else w - margin - tw
            draw.text((x, y), wrapped, font=font, fill=ink)
            y += line_px
    return img


def _extend(img, extra):
    w, h = img.size
    new = Image.new("RGB", (w, h + extra), PAPER)
    new.paste(img, (0, 0))
    return new, ImageDraw.Draw(new), h + extra


def _wrap(draw, text, font, width):
    if not text:
        return [""]
    words = text.split(" ")
    out, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= width or not cur:
            cur = trial
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


PROFILES = {
    "good": dict(tilt=0.03, rot=1.5, blur=0.4, dark=0.95, grad=0.08, noise=3, fill=0.85, jpeg=0.75),
    "typical": dict(tilt=0.07, rot=4.0, blur=0.9, dark=0.85, grad=0.18, noise=6, fill=0.72, jpeg=0.75),
    "poor": dict(tilt=0.12, rot=7.0, blur=1.5, dark=0.70, grad=0.30, noise=10, fill=0.60, jpeg=0.75),
}


def _solve(A, B):
    """Gaussian elimination with partial pivoting; A is n x n, B length n."""
    n = len(A)
    M = [row[:] + [B[i]] for i, row in enumerate(A)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c and M[r][c]:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def _persp_coeffs(src, dst):
    matrix, rhs = [], []
    for (x, y), (u, v) in zip(src, dst):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs += [u, v]
    return tuple(_solve(matrix, rhs))


def degrade(paper: Image.Image, profile: str = "typical", seed: int = 0,
            frame_size=(1024, 768)) -> bytes:
    """Return JPEG bytes of a camera-style frame containing the paper."""
    p = PROFILES[profile]
    rng = random.Random(seed)
    fw, fh = frame_size

    # Work at 2x the final frame so blur/noise look like sensor effects after downsizing.
    W, H = fw * 2, fh * 2
    base = rng.choice([(96, 78, 62), (150, 142, 130), (70, 75, 80), (190, 180, 165)])
    bg = Image.new("RGB", (W, H), base)
    bd = ImageDraw.Draw(bg)
    for i in range(0, W, 8):
        k = 1 + (i / W - 0.5) * 0.25
        bd.rectangle([i, 0, i + 8, H], fill=tuple(min(255, int(c * k)) for c in base))
    bg = bg.filter(ImageFilter.GaussianBlur(30))

    pw, ph = paper.size
    scale = min(W * p["fill"] / pw, H * p["fill"] / ph)
    paper = paper.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
    pw, ph = paper.size

    t = p["tilt"]

    def jit(s):
        return abs(rng.uniform(-t, t) * s)

    src = [(0, 0), (pw, 0), (pw, ph), (0, ph)]
    dst = [(jit(pw), jit(ph)), (pw - jit(pw), jit(ph)),
           (pw - jit(pw), ph - jit(ph)), (jit(pw), ph - jit(ph))]
    layer = paper.convert("RGBA")
    coeffs = _persp_coeffs(dst, src)
    layer = layer.transform((pw, ph), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    layer = layer.rotate(rng.uniform(-p["rot"], p["rot"]), resample=Image.BICUBIC, expand=True)

    lw, lh = layer.size
    # Build the light gradient on a canvas twice the size so that rotating it
    # never exposes an unlit corner, then crop the centre back to the layer.
    gw, gh = lw * 2, lh * 2
    grad = Image.new("L", (gw, gh), 255)
    gd = ImageDraw.Draw(grad)
    g = p["grad"]
    for i in range(gw):
        v = int(255 * (1 - g * (i / gw)))
        gd.line([(i, 0), (i, gh)], fill=v)
    grad = grad.rotate(rng.uniform(0, 360), resample=Image.BILINEAR)
    grad = grad.crop((lw // 2, lh // 2, lw // 2 + lw, lh // 2 + lh))
    rgb = layer.convert("RGB")
    rgb = Image.composite(rgb, Image.new("RGB", rgb.size, (0, 0, 0)), grad)
    rgb = ImageEnhance.Brightness(rgb).enhance(p["dark"])
    layer = Image.merge("RGBA", (*rgb.split(), layer.split()[3]))

    ox = (W - lw) // 2 + int(rng.uniform(-0.04, 0.04) * W)
    oy = (H - lh) // 2 + int(rng.uniform(-0.04, 0.04) * H)
    ox, oy = max(0, ox), max(0, oy)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 110), (ox + 14, oy + 18), layer.split()[3])
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    frame = bg.convert("RGBA")
    frame.alpha_composite(shadow)
    frame.alpha_composite(layer, (ox, oy))
    frame = frame.convert("RGB")

    frame = frame.filter(ImageFilter.GaussianBlur(p["blur"] * 2))
    frame = frame.resize((fw, fh), Image.LANCZOS)
    if p["noise"]:
        # Pillow's effect_noise is Gaussian around 128; blend it in as sensor grain.
        grain = Image.effect_noise((fw, fh), p["noise"] * 2).convert("RGB")
        frame = Image.blend(frame, grain, alpha=p["noise"] / 60)
    frame = frame.filter(ImageFilter.GaussianBlur(p["blur"] * 0.3))

    buf = io.BytesIO()
    frame.save(buf, "JPEG", quality=int(p["jpeg"] * 100))
    return buf.getvalue()


def post(frame_jpeg: bytes, timeout: float = 90.0) -> dict:
    """POST one frame to /read_document exactly as the browser does."""
    started = time.monotonic()
    r = httpx.post(f"{BACKEND}/read_document",
                   files={"image": ("frame.jpg", frame_jpeg, "image/jpeg")}, timeout=timeout)
    out = {"http": r.status_code, "wall_s": round(time.monotonic() - started, 2)}
    try:
        out.update(r.json())
    except Exception:
        out["body"] = r.text[:500]
    return out


def run_case(name: str, lines, size_mm=(100, 140), profile: str = "typical", seed: int = 0,
             truth: dict | None = None, frame_size=(1024, 768)) -> dict:
    """Render, degrade, post, and save everything under OUT_DIR/<name>-<profile>."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paper = render(lines, size_mm=size_mm)
    frame = degrade(paper, profile=profile, seed=seed, frame_size=frame_size)
    stem = OUT_DIR / f"{name}-{profile}"
    paper.save(f"{stem}-paper.png")
    Path(f"{stem}-frame.jpg").write_bytes(frame)
    result = post(frame)
    record = {"name": name, "profile": profile, "seed": seed, "size_mm": list(size_mm),
              "frame_bytes": len(frame), "truth": truth, "result": result}
    Path(f"{stem}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


if __name__ == "__main__":
    demo = [("hwb", "Back at 3pm"), ("hw", "Call Dr Patel 0117 496 0742"), ("hw", "re: Friday blood test")]
    for prof in ("good", "typical", "poor"):
        rec = run_case("smoke-sticky", demo, size_mm=(76, 76), profile=prof, seed=1)
        print(prof, rec["result"].get("http"), rec["result"].get("elapsed_s"))
        print(rec["result"].get("text"))
        print()
