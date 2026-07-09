import React from "react";
import LogInteractionForm from "./components/LogInteractionForm";
import ChatPanel from "./components/ChatPanel";
import "./App.css";

export default function App() {
  return (
    <div className="app-shell">
      <div className="form-column">
        <LogInteractionForm />
      </div>
      <div className="chat-column">
        <ChatPanel />
      </div>
    </div>
  );
}
