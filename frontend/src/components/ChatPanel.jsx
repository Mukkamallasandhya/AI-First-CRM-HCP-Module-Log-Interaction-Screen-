import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { addUserMessage, sendMessage } from "../store/slices/chatSlice";

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, pending } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    dispatch(addUserMessage(text));
    dispatch(sendMessage(text));
    setInput("");
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="chat-avatar">🤖</span>
        <div>
          <div className="chat-title">AI Assistant</div>
          <div className="chat-subtitle">Log Interaction details here via chat</div>
        </div>
      </div>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble-row ${m.role}`}>
            <div className={`chat-bubble ${m.role}`}>
              {m.text}
              {m.toolCalls && m.toolCalls.length > 0 && (
                <div className="tool-badge-row">
                  {m.toolCalls.map((t) => (
                    <span className="tool-badge" key={t}>
                      ✓ {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {pending && (
          <div className="chat-bubble-row assistant">
            <div className="chat-bubble assistant typing">Thinking...</div>
          </div>
        )}
      </div>

      <div className="chat-input-row">
        <input
          className="chat-input"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button className="chat-send-btn" onClick={handleSend} disabled={pending}>
          Log
        </button>
      </div>
    </div>
  );
}
