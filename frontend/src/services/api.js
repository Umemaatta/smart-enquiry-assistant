import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/**
 * Sends a question to the Smart Enquiry Assistant backend and
 * returns { answer, sources }. The backend (src/api.py) does all the
 * retrieval and answer generation — this file only talks to it.
 */
export async function askQuestion(question) {
  const response = await axios.post(`${API_URL}/ask`, { question });
  return response.data;
}
