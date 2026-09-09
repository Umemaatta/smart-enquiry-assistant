import { useEffect, useRef } from "react";
import Message from "./Message.jsx";
import WelcomeScreen from "./WelcomeScreen.jsx";
import "../styles/ChatWindow.css";

export default function ChatWindow({ messages, loading, onExampleClick }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const isEmpty = messages.length === 0;

  return (
    <div className={`chat-window ${isEmpty ? "empty" : ""}`}>
      {isEmpty ? (
        <WelcomeScreen onExampleClick={onExampleClick} />
      ) : (
        <div className="chat-messages">
          {messages.map((message, index) => (
            <Message key={index} message={message} />
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="message-avatar assistant">AI</div>
              <div className="message-bubble assistant typing-bubble">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
