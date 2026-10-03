/**
 * Camera frame preparation for the vision model.
 *
 * A phone screen held up to the webcam reads fine: it is bright, backlit and
 * high-contrast. Real paper under room light is not. It arrives dim, low
 * contrast, slightly motion-blurred, and occupying maybe a third of the frame,
 * so most of the pixels the model receives are desk, not text. This module
 * fixes those four things before upload:
 *
 *   1. Sharpest of several frames: grab a few frames over ~300ms and keep the
 *      one with the most edge energy, so a hand tremor does not decide the read.
 *   2. Paper crop: find the bright rectangular region (paper on a darker
 *      background) and crop to it with a margin, so the model's pixels go on
 *      the text. If no clear region is found, the whole frame is sent.
 *   3. Auto-levels: stretch the luminance so the paper is white and the ink is
 *      black, which is what a dim room and a webcam's auto-exposure take away.
 *   4. Resolution: the crop is sent at up to MAX_WIDTH px wide, never upscaled.
 */

export const MAX_WIDTH = 1280;
export const JPEG_QUALITY = 0.85;
const BURST = 3;
const BURST_GAP_MS = 110;
const THUMB_W = 160;

type Box = { x: number; y: number; w: number; h: number };

function drawVideo(video: HTMLVideoElement): HTMLCanvasElement {
  const c = document.createElement("canvas");
  c.width = video.videoWidth;
  c.height = video.videoHeight;
  c.getContext("2d")!.drawImage(video, 0, 0);
  return c;
}

function thumbnail(src: HTMLCanvasElement): ImageData {
  const scale = THUMB_W / src.width;
  const c = document.createElement("canvas");
  c.width = THUMB_W;
  c.height = Math.max(1, Math.round(src.height * scale));
  const ctx = c.getContext("2d")!;
  ctx.drawImage(src, 0, 0, c.width, c.height);
  return ctx.getImageData(0, 0, c.width, c.height);
}

function luminance(d: ImageData): Float32Array {
  const out = new Float32Array(d.width * d.height);
  const p = d.data;
  for (let i = 0, j = 0; i < p.length; i += 4, j++) {
    out[j] = 0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2];
  }
  return out;
}

/** Sum of absolute gradients: higher means sharper. */
function sharpness(lum: Float32Array, w: number, h: number): number {
  let s = 0;
  for (let y = 1; y < h; y++) {
    for (let x = 1; x < w; x++) {
      const i = y * w + x;
      s += Math.abs(lum[i] - lum[i - 1]) + Math.abs(lum[i] - lum[i - w]);
    }
  }
  return s;
}

/**
 * Otsu's threshold over the luminance histogram, then the largest contiguous
 * run of rows and columns that are mostly "bright". Returns null when the
 * bright region is nearly the whole frame (nothing to gain) or too small to be
 * a document (probably a highlight).
 */
function findPaper(lum: Float32Array, w: number, h: number): Box | null {
  const hist = new Array<number>(256).fill(0);
  for (let i = 0; i < lum.length; i++) hist[Math.min(255, Math.max(0, lum[i] | 0))]++;
  const total = lum.length;
  let sum = 0;
  for (let t = 0; t < 256; t++) sum += t * hist[t];
  let sumB = 0, wB = 0, best = 0, thresh = 128;
  for (let t = 0; t < 256; t++) {
    wB += hist[t];
    if (!wB) continue;
    const wF = total - wB;
    if (!wF) break;
    sumB += t * hist[t];
    const mB = sumB / wB, mF = (sum - sumB) / wF;
    const between = wB * wF * (mB - mF) ** 2;
    if (between > best) { best = between; thresh = t; }
  }
  // Paper must be meaningfully brighter than the background; otherwise the
  // frame is one flat tone (a phone screen filling the view, say) and we leave it.
  if (thresh < 60) return null;

  const rowFrac = new Float32Array(h), colFrac = new Float32Array(w);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (lum[y * w + x] > thresh) { rowFrac[y] += 1 / w; colFrac[x] += 1 / h; }
    }
  }
  const run = (frac: Float32Array, min: number): [number, number] | null => {
    let bestStart = -1, bestLen = 0, start = -1;
    for (let i = 0; i <= frac.length; i++) {
      const on = i < frac.length && frac[i] >= min;
      if (on && start < 0) start = i;
      if (!on && start >= 0) {
        if (i - start > bestLen) { bestLen = i - start; bestStart = start; }
        start = -1;
      }
    }
    return bestLen ? [bestStart, bestLen] : null;
  };
  const rows = run(rowFrac, 0.12);
  const cols = run(colFrac, 0.12);
  if (!rows || !cols) return null;

  const box = { x: cols[0], y: rows[0], w: cols[1], h: rows[1] };
  const area = (box.w * box.h) / (w * h);
  if (area > 0.85 || area < 0.04) return null;
  return box;
}

/** Linear stretch so the 1st percentile goes to black and the 99th to white. */
function autoLevels(ctx: CanvasRenderingContext2D, w: number, h: number): void {
  const img = ctx.getImageData(0, 0, w, h);
  const p = img.data;
  const hist = new Array<number>(256).fill(0);
  for (let i = 0; i < p.length; i += 4) {
    hist[(0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2]) | 0]++;
  }
  const n = w * h;
  let lo = 0, hi = 255, acc = 0;
  for (let t = 0; t < 256; t++) { acc += hist[t]; if (acc > n * 0.01) { lo = t; break; } }
  acc = 0;
  for (let t = 255; t >= 0; t--) { acc += hist[t]; if (acc > n * 0.01) { hi = t; break; } }
  if (hi - lo < 40) return; // already flat or already stretched; leave it
  const k = 255 / (hi - lo);
  const lut = new Uint8ClampedArray(256);
  for (let t = 0; t < 256; t++) lut[t] = Math.max(0, Math.min(255, Math.round((t - lo) * k)));
  for (let i = 0; i < p.length; i += 4) {
    p[i] = lut[p[i]];
    p[i + 1] = lut[p[i + 1]];
    p[i + 2] = lut[p[i + 2]];
  }
  ctx.putImageData(img, 0, 0);
}

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface Prepared {
  blob: Blob;
  cropped: boolean;
  width: number;
  height: number;
}

/**
 * Grab the best frame from the video, crop it to the document, fix its levels
 * and encode it. Returns null if the video is not producing frames yet.
 */
export async function prepareFrame(video: HTMLVideoElement): Promise<Prepared | null> {
  if (!video.videoWidth) return null;

  // 1. Sharpest of a short burst.
  let bestCanvas: HTMLCanvasElement | null = null;
  let bestThumb: ImageData | null = null;
  let bestScore = -1;
  for (let i = 0; i < BURST; i++) {
    const c = drawVideo(video);
    const t = thumbnail(c);
    const score = sharpness(luminance(t), t.width, t.height);
    if (score > bestScore) { bestScore = score; bestCanvas = c; bestThumb = t; }
    if (i < BURST - 1) await wait(BURST_GAP_MS);
  }
  if (!bestCanvas || !bestThumb) return null;

  // 2. Crop to the paper, with a margin, scaled back to full-frame coordinates.
  const lum = luminance(bestThumb);
  const box = findPaper(lum, bestThumb.width, bestThumb.height);
  const sx = bestCanvas.width / bestThumb.width;
  const sy = bestCanvas.height / bestThumb.height;
  let crop: Box = { x: 0, y: 0, w: bestCanvas.width, h: bestCanvas.height };
  if (box) {
    const mx = box.w * 0.06, my = box.h * 0.06;
    const x0 = Math.max(0, (box.x - mx) * sx);
    const y0 = Math.max(0, (box.y - my) * sy);
    const x1 = Math.min(bestCanvas.width, (box.x + box.w + mx) * sx);
    const y1 = Math.min(bestCanvas.height, (box.y + box.h + my) * sy);
    crop = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }

  // 3 + 4. Output canvas at most MAX_WIDTH wide, never upscaled; then levels.
  const scale = Math.min(1, MAX_WIDTH / crop.w);
  const out = document.createElement("canvas");
  out.width = Math.round(crop.w * scale);
  out.height = Math.round(crop.h * scale);
  const ctx = out.getContext("2d")!;
  ctx.drawImage(bestCanvas, crop.x, crop.y, crop.w, crop.h, 0, 0, out.width, out.height);
  autoLevels(ctx, out.width, out.height);

  const blob = await new Promise<Blob | null>((resolve) =>
    out.toBlob((b) => resolve(b), "image/jpeg", JPEG_QUALITY),
  );
  if (!blob) return null;
  return { blob, cropped: !!box, width: out.width, height: out.height };
}
