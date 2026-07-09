import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE });

export const searchHCPs = (q) => client.get("/api/hcps", { params: { q } }).then((r) => r.data);

export const createInteraction = (payload) => client.post("/api/interactions", payload).then((r) => r.data);

export const updateInteraction = (id, payload) => client.patch(`/api/interactions/${id}`, payload).then((r) => r.data);

export const listInteractions = () => client.get("/api/interactions").then((r) => r.data);

export const getInteraction = (id) => client.get(`/api/interactions/${id}`).then((r) => r.data);

export const sendChatMessage = (message, sessionId, currentFormState) =>
  client
    .post("/api/chat", { message, session_id: sessionId, current_form_state: currentFormState })
    .then((r) => r.data);

export default client;
