import { useRef, useState } from "react";
import "../styles/MessageInput.css";

export default function MessageInput({ onSend, loading }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || loading) return;

    onSend(trimmed);
    setValue("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  function handleChange(event) {
    setValue(event.target.value);

    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    }
  }

  return (
    <div className="message-input-wrapper">
      <div className="message-input-box">
        <textarea
          ref={textareaRef}
          className="message-input-textarea"
          placeholder="Ask anything about QUEST University..."
          rows={1}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
        />

        <button
          className="message-send-btn"
          onClick={submit}
          disabled={loading || value.trim().length === 0}
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>

      <p className="message-input-hint">
        Press Enter to send · Shift + Enter for a new line
      </p>
    </div>
  );
}
