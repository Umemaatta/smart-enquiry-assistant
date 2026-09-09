import "../styles/Sidebar.css";

export default function Sidebar({
  chats,
  activeChatId,
  isOpen,
  onNewChat,
  onSelectChat,
  onClearChat,
  onDeleteChat,
  onClose,
}) {
  return (
    <>
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}

      <aside className={`sidebar ${isOpen ? "sidebar-open" : ""}`}>
        <button className="sidebar-new-chat" onClick={onNewChat}>
          + New Chat
        </button>

        <div className="sidebar-section">
          <p className="sidebar-section-title">Chat History</p>

          <div className="sidebar-history-list">
            {chats.map((chat) => (
              <div
                key={chat.id}
                className={`sidebar-history-item ${
                  chat.id === activeChatId ? "active" : ""
                }`}
              >
                <button
                  className="sidebar-history-btn"
                  onClick={() => onSelectChat(chat.id)}
                  title={chat.title}
                >
                  {chat.title || "New Chat"}
                </button>

                <button
                  className="sidebar-history-delete"
                  onClick={() => onDeleteChat(chat.id)}
                  aria-label="Delete chat"
                  title="Delete chat"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        <button className="sidebar-clear-chat" onClick={onClearChat}>
          Clear Current Chat
        </button>

        <div className="sidebar-about">
          <p className="sidebar-section-title">About</p>
          <p>
            This assistant answers questions using official QUEST University
            documents only. If information isn't available in those
            documents, it will let you know instead of guessing.
          </p>
        </div>
      </aside>
    </>
  );
}
