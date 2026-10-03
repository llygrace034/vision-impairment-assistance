import { useCallback, useEffect, useRef, useState } from "react";
import { useConversation } from "@elevenlabs/react";
import { prepareFrame } from "./capture";
import "./App.css";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [lastRead, setLastRead] = useState<string | null>(null);
  const [lastFrame, setLastFrame] = useState<string | null>(null);
  const [reading, setReading] = useState(false);

  /**
   * Grab the best of a short burst of frames, crop it to the paper and fix
   * the levels (see capture.ts). Paper under room light is dim and low
   * contrast and fills a third of the frame; a phone screen is neither, which
   * is why the phone read and the paper did not before this.
   */
  const captureFrame = useCallback(async (): Promise<Blob | null> => {
    const video = videoRef.current;
    if (!video) return null;
    const prepared = await prepareFrame(video);
    if (!prepared) return null;
    setLastFrame((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(prepared.blob);
    });
    return prepared.blob;
  }, []);

  /**
   * The client tool the agent calls. Because this runs in the browser, the
   * frame is already here -- there is nothing to correlate against a separate
   * webhook request, which is why this is a client tool and not a server tool.
   *
   * Must return a string: ClientToolResult is `string | number | void`, and an
   * object would not reach the agent. Any failure is returned as a sentence the
   * agent can say out loud, never thrown, because a throw makes it apologise
   * with no idea what went wrong.
   */
  const readDocument = useCallback(async (): Promise<string> => {
    setReading(true);
    try {
      const frame = await captureFrame();
      if (!frame) return "The camera is not ready yet. Please try again in a moment.";

      const form = new FormData();
      form.append("image", frame, "frame.jpg");

      const res = await fetch(`${BACKEND}/read_document`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) return "I had trouble reading that. Please try again.";

      const data = await res.json();
      const text: string = data.text ?? "I could not read that.";
      setLastRead(text);
      return text;
    } catch {
      return "I could not reach the reader. Please check the connection and try again.";
    } finally {
      setReading(false);
    }
  }, [captureFrame]);

  const conversation = useConversation({
    clientTools: { read_document: readDocument },
    onError: (message) => setCameraError(String(message)),
  });

  const { status, isSpeaking, startSession, endSession } = conversation;
  const connected = status === "connected";

  // Camera starts on mount so the user can aim the letter before connecting.
  useEffect(() => {
    let cancelled = false;
    navigator.mediaDevices
      .getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1920 } },
        audio: false,
      })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch((e) => setCameraError(`Camera unavailable: ${e.message}`));

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const start = useCallback(async () => {
    setCameraError(null);
    try {
      // Mic permission must be granted before the session opens.
      await navigator.mediaDevices.getUserMedia({ audio: true });
      const res = await fetch(`${BACKEND}/signed-url`);
      if (!res.ok) throw new Error(`token request failed (${res.status})`);
      const { token } = await res.json();
      startSession({ conversationToken: token, connectionType: "webrtc" });
    } catch (e) {
      setCameraError(e instanceof Error ? e.message : String(e));
    }
  }, [startSession]);

  const statusLine = reading
    ? "Reading the letter…"
    : isSpeaking
      ? "EasyRead is speaking…"
      : connected
        ? "Listening — hold up a letter and ask what it says"
        : status === "connecting"
          ? "Connecting…"
          : "Not connected";

  return (
    <main className="app">
      <h1>EasyRead</h1>

      <div className="viewport">
        <video ref={videoRef} autoPlay playsInline muted aria-label="Camera preview" />
        {reading && <div className="reading-badge">Reading…</div>}
      </div>

      {/* aria-live so a screen reader announces state changes without focus. */}
      <p className="status" role="status" aria-live="polite">
        {statusLine}
      </p>

      <button
        className={connected ? "btn btn-stop" : "btn btn-start"}
        onClick={connected ? endSession : start}
      >
        {connected ? "Stop" : "Start talking"}
      </button>

      {cameraError && (
        <p className="error" role="alert">
          {cameraError}
        </p>
      )}

      {lastRead && (
        <section className="transcript" aria-label="What the camera read">
          <h2>Last read</h2>
          {lastFrame && (
            <img className="sent-frame" src={lastFrame} alt="The frame that was sent to the reader" />
          )}
          <pre>{lastRead}</pre>
        </section>
      )}
    </main>
  );
}
