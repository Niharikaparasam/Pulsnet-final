// src/components/ChatWidget.jsx
import React, { useState, useRef, useEffect } from "react";
import { apiClient } from "../api";
import { useAuth } from "../AuthContext";

export default function ChatWidget() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hello! I'm PulseBot. Ask me about donating, matching or CSV formats." }
  ]);
  const [text, setText] = useState("");
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const sendMessage = async () => {
    if (!text.trim()) return;
    const userMsg = { from: "user", text: text.trim() };
    setMessages((m) => [...m, userMsg]);
    setText("");

    try {
      const payload = { message: userMsg.text, user_id: user?.email };
      const res = await apiClient.post("/api/chat/", payload);
      const botText = res.data.response;
      setMessages((m) => [...m, { from: "bot", text: botText }]);
      speak(botText);
    } catch (err) {
      console.error(err);
      setMessages((m) => [...m, { from: "bot", text: "Chat failed — please try again later." }]);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  function speak(t) {
    if (!window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(t);
    u.lang = "en-IN";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }

  return (
    <>
      <div
        onClick={() => setOpen(!open)}
        style={{
          position: "fixed", right: 20, bottom: 20, zIndex: 1200,
          width: 56, height: 56, borderRadius: 28, background: "#ffcb3c",
          display: "flex", alignItems: "center", justifyContent: "center",
          cursor: "pointer",
        }}
        aria-label="Open chat"
      >
        {open ? "✖" : "💬"}
      </div>

      {open && (
        <div style={{
          position: "fixed", right: 20, bottom: 92, zIndex: 1200,
          width: 360, maxHeight: 520, borderRadius: 12, overflow: "hidden",
          boxShadow: "0 10px 30px rgba(0,0,0,0.15)", display: "flex", flexDirection: "column",
          background: "#fff"
        }}>
          <div style={{ padding: 12, fontWeight: 700, background: "#111827", color: "#fff" }}>
            PulseNet Assistant
          </div>

          <div style={{ padding: 12, overflow: "auto", flex: 1 }}>
            {messages.map((m, i) => (
              <div key={i} style={{ marginBottom: 8, textAlign: m.from === "user" ? "right" : "left" }}>
                <div style={{
                  display: "inline-block", padding: "8px 12px", borderRadius: 12,
                  background: m.from === "user" ? "#2563eb" : "#f3f4f6",
                  color: m.from === "user" ? "#fff" : "#111"
                }}>
                  {m.text}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          <div style={{ padding: 10, borderTop: "1px solid #eee", display: "flex", gap: 8 }}>
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask: 'How to donate' or 'CSV format'..."
              style={{ flex: 1, padding: 8, borderRadius: 8, border: "1px solid #ddd" }}
            />
            <button onClick={sendMessage} style={{ padding: "8px 12px", borderRadius: 8, background: "#111", color: "#fff", border: "none" }}>
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}
