import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChatMessage, getInteraction } from "../../api/client";
import { applyAgentUpdate } from "./interactionSlice";

const initialState = {
  sessionId: `session-${Date.now()}`,
  messages: [
    {
      role: "assistant",
      text: 'Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.',
    },
  ],
  pending: false,
};

export const sendMessage = createAsyncThunk(
  "chat/send",
  async (text, { getState, dispatch }) => {
    const state = getState();
    const response = await sendChatMessage(text, state.chat.sessionId, state.interaction);

    // If a tool actually logged/edited an interaction, pull the saved record back
    // from the backend and push its real field values into the structured form.
    const loggedOrEdited =
      response.tool_calls.includes("log_interaction") || response.tool_calls.includes("edit_interaction");

    if (loggedOrEdited && response.interaction_id) {
      const saved = await getInteraction(response.interaction_id);
      dispatch(
        applyAgentUpdate({
          interaction_id: saved.id,
          hcp_name: saved.hcp_name_raw,
          interaction_type: saved.interaction_type,
          topics_discussed: saved.topics_discussed,
          sentiment: saved.sentiment,
          materials_shared: (saved.materials || []).map((m) => m.name),
        })
      );
    }
    return response;
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ role: "user", text: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.pending = true;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.pending = false;
        state.messages.push({
          role: "assistant",
          text: action.payload.reply,
          toolCalls: action.payload.tool_calls,
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.pending = false;
        state.messages.push({
          role: "assistant",
          text: `Sorry, something went wrong: ${action.error.message}`,
        });
      });
  },
});

export const { addUserMessage } = chatSlice.actions;
export default chatSlice.reducer;