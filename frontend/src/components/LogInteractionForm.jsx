import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  setField,
  addAttendee,
  removeAttendee,
  addMaterial,
  removeMaterial,
  saveInteraction,
} from "../store/slices/interactionSlice";
import HCPSearch from "./HCPSearch";

const INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference", "Sample Drop"];
const SENTIMENTS = ["Positive", "Neutral", "Negative"];

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.interaction);
  const [attendeeInput, setAttendeeInput] = useState("");
  const [materialInput, setMaterialInput] = useState("");
  const [consentGiven, setConsentGiven] = useState(false);
  const [voiceNoteMode, setVoiceNoteMode] = useState(false);

  const update = (field) => (e) => dispatch(setField({ field, value: e.target.value }));

  const handleAddAttendee = () => {
    if (attendeeInput.trim()) {
      dispatch(addAttendee(attendeeInput.trim()));
      setAttendeeInput("");
    }
  };

  const handleAddMaterial = () => {
    if (materialInput.trim()) {
      dispatch(addMaterial(materialInput.trim()));
      setMaterialInput("");
    }
  };

  const handleSave = () => {
    dispatch(saveInteraction());
  };

  return (
    <div className="form-panel">
      <h1 className="form-title">Log HCP Interaction</h1>

      <section className="form-section">
        <h2 className="section-label">Interaction Details</h2>

        <div className="form-grid-2">
          <div className="field">
            <label>HCP Name</label>
            <HCPSearch value={form.hcpName} />
          </div>
          <div className="field">
            <label>Interaction Type</label>
            <select className="text-input" value={form.interactionType} onChange={update("interactionType")}>
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-grid-2">
          <div className="field">
            <label>Date</label>
            <input type="date" className="text-input" value={form.date} onChange={update("date")} />
          </div>
          <div className="field">
            <label>Time</label>
            <input type="time" className="text-input" value={form.time} onChange={update("time")} />
          </div>
        </div>

        <div className="field">
          <label>Attendees</label>
          <div className="chip-input-row">
            <input
              className="text-input"
              placeholder="Enter names or search..."
              value={attendeeInput}
              onChange={(e) => setAttendeeInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddAttendee()}
            />
            <button className="btn-secondary" onClick={handleAddAttendee}>
              Add
            </button>
          </div>
          <div className="chip-row">
            {form.attendees.map((a) => (
              <span className="chip" key={a}>
                {a}
                <button className="chip-remove" onClick={() => dispatch(removeAttendee(a))}>
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        <div className="field">
          <label>Topics Discussed</label>
          <textarea
            className="text-input textarea"
            placeholder="Enter key discussion points..."
            value={form.topicsDiscussed}
            onChange={update("topicsDiscussed")}
            rows={4}
          />
          <button className="link-btn" onClick={() => setVoiceNoteMode((v) => !v)}>
            🎙 Summarize from Voice Note (Requires Consent)
          </button>
          {voiceNoteMode && (
            <div className="voice-note-box">
              <label className="consent-row">
                <input type="checkbox" checked={consentGiven} onChange={(e) => setConsentGiven(e.target.checked)} />
                I have the HCP's consent to record/summarize this note.
              </label>
              <p className="hint-text">
                Voice note capture &amp; transcription isn't wired to a mic in this demo build — paste a transcript into
                the chat panel and ask the assistant to "summarize this voice note" to see the same extraction pipeline
                run via the <code>summarize_voice_note</code> tool.
              </p>
            </div>
          )}
        </div>

        <div className="field">
          <label>Sentiment</label>
          <div className="pill-row">
            {SENTIMENTS.map((s) => (
              <button
                key={s}
                className={`pill ${form.sentiment === s ? `pill-active pill-${s.toLowerCase()}` : ""}`}
                onClick={() => dispatch(setField({ field: "sentiment", value: s }))}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label>Materials Shared / Samples Distributed</label>
          <div className="chip-input-row">
            <input
              className="text-input"
              placeholder="Materials shared..."
              value={materialInput}
              onChange={(e) => setMaterialInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddMaterial()}
            />
            <button className="btn-secondary" onClick={handleAddMaterial}>
              Search/Add
            </button>
          </div>
          <div className="chip-row">
            {form.materials.map((m, i) => (
              <span className="chip" key={`${m.name}-${i}`}>
                {m.name}
                <button className="chip-remove" onClick={() => dispatch(removeMaterial(i))}>
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        <div className="form-grid-2">
          <div className="field">
            <label>Follow-up Notes</label>
            <input
              className="text-input"
              placeholder="Optional follow-up notes..."
              value={form.followUpNotes}
              onChange={update("followUpNotes")}
            />
          </div>
          <div className="field">
            <label>Follow-up Date</label>
            <input type="date" className="text-input" value={form.followUpDate} onChange={update("followUpDate")} />
          </div>
        </div>
      </section>

      <div className="form-footer">
        {form.status === "saved" && <span className="save-status success">Saved ✓</span>}
        {form.status === "error" && <span className="save-status error">{form.error}</span>}
        <button className="btn-primary" onClick={handleSave} disabled={form.status === "saving" || !form.hcpName}>
          {form.status === "saving" ? "Saving..." : "Save Interaction"}
        </button>
      </div>
    </div>
  );
}
