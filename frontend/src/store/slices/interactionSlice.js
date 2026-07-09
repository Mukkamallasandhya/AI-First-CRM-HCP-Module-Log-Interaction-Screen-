import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { createInteraction, updateInteraction } from "../../api/client";

const todayISO = new Date().toISOString().slice(0, 10);
const nowTime = new Date().toTimeString().slice(0, 5);

const initialState = {
  id: null, // set once saved, so the chat agent can target edit_interaction on this record
  hcpName: "",
  interactionType: "Meeting",
  date: todayISO,
  time: nowTime,
  attendees: [],
  topicsDiscussed: "",
  sentiment: "",
  materials: [], // [{ name, quantity }]
  followUpNotes: "",
  followUpDate: "",
  status: "idle", // idle | saving | saved | error
  error: null,
};

export const saveInteraction = createAsyncThunk("interaction/save", async (_, { getState }) => {
  const s = getState().interaction;
  const payload = {
    hcp_name: s.hcpName,
    interaction_type: s.interactionType,
    date: `${s.date}T${s.time}:00`,
    attendees: s.attendees,
    topics_discussed: s.topicsDiscussed,
    sentiment: s.sentiment || null,
    materials: s.materials,
    follow_up_notes: s.followUpNotes || null,
    follow_up_date: s.followUpDate ? `${s.followUpDate}T00:00:00` : null,
  };
  if (s.id) {
    return updateInteraction(s.id, payload);
  }
  return createInteraction(payload);
});

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    setField(state, action) {
      const { field, value } = action.payload;
      state[field] = value;
    },
    addAttendee(state, action) {
      if (action.payload && !state.attendees.includes(action.payload)) {
        state.attendees.push(action.payload);
      }
    },
    removeAttendee(state, action) {
      state.attendees = state.attendees.filter((a) => a !== action.payload);
    },
    addMaterial(state, action) {
      state.materials.push({ name: action.payload, quantity: "1" });
    },
    removeMaterial(state, action) {
      state.materials.splice(action.payload, 1);
    },
    /** Merge fields pushed in by the AI assistant after it calls log_interaction / edit_interaction. */
    applyAgentUpdate(state, action) {
      const u = action.payload;
      if (u.hcp_name) state.hcpName = u.hcp_name;
      if (u.interaction_type) state.interactionType = u.interaction_type;
      if (u.topics_discussed) state.topicsDiscussed = u.topics_discussed;
      if (u.sentiment) state.sentiment = u.sentiment;
      if (u.materials_shared) {
        state.materials = u.materials_shared.map((m) => ({ name: m, quantity: "1" }));
      }
      if (u.interaction_id) state.id = u.interaction_id;
    },
    resetForm() {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(saveInteraction.pending, (state) => {
        state.status = "saving";
        state.error = null;
      })
      .addCase(saveInteraction.fulfilled, (state, action) => {
        state.status = "saved";
        state.id = action.payload.id;
      })
      .addCase(saveInteraction.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message;
      });
  },
});

export const {
  setField,
  addAttendee,
  removeAttendee,
  addMaterial,
  removeMaterial,
  applyAgentUpdate,
  resetForm,
} = interactionSlice.actions;

export default interactionSlice.reducer;
