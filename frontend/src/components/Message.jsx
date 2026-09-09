import Sources from "./Sources.jsx";
import "../styles/Message.css";

export default function Message({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`message-avatar ${isUser ? "user" : "assistant"}`}>
        {isUser ? "You" : "AI"}
      </div>

      <div className={`message-bubble ${isUser ? "user" : "assistant"}`}>
        <div className="message-content">{message.content}</div>

        {!isUser && <Sources sources={message.sources} />}
      </div>
    </div>
  );
}
