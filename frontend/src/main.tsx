import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ConversationProvider } from "@elevenlabs/react";
import App from "./App.tsx";
import "./index.css";

// @elevenlabs/react 1.16: useConversation() throws unless it is inside a
// ConversationProvider. Earlier versions of the SDK did not require this.
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ConversationProvider>
      <App />
    </ConversationProvider>
  </StrictMode>,
);
