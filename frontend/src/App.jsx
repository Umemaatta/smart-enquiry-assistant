import { useEffect, useState } from "react";
import Header from "./components/Header.jsx";
import Sidebar from "./components/Sidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import MessageInput from "./components/MessageInput.jsx";
import { askQuestion } from "./services/api.js";
import "./styles/App.css";

const STORAGE_KEY = "quest-smart-enquiry-chats";

// crypto.randomUUID() only exists in secure contexts (https / localhost),
// so fall back to a simple id when opening the app over a plain LAN address.
function createId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createEmptyChat() {
  return {
    id: createId(),
    title: "New Chat",
    messages: [],
  };
}

function loadChatsFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    return null;
  } catch {
    return null;
  }
}

export default function App() {
  const [chats, setChats] = useState(() => loadChatsFromStorage() || [createEmptyChat()]);
  const [activeChatId, setActiveChatId] = useState(() => chats[0].id);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
    } catch {
      // localStorage may be unavailable (private browsing, etc.) - safe to ignore
    }
  }, [chats]);

  const activeChat = chats.find((chat) => chat.id === activeChatId) || chats[0];

  function updateChat(chatId, updater) {
    setChats((prev) =>
      prev.map((chat) => (chat.id === chatId ? updater(chat) : chat))
    );
  }

  function handleNewChat() {
    const newChat = createEmptyChat();
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(newChat.id);
    setSidebarOpen(false);
  }

  function handleSelectChat(chatId) {
    setActiveChatId(chatId);
    setSidebarOpen(false);
  }

  function handleClearChat() {
    updateChat(activeChat.id, (chat) => ({
      ...chat,
      title: "New Chat",
      messages: [],
    }));
  }

  function handleDeleteChat(chatId) {
    setChats((prev) => {
      const remaining = prev.filter((chat) => chat.id !== chatId);
      const nextChats = remaining.length > 0 ? remaining : [createEmptyChat()];

      if (chatId === activeChatId) {
        setActiveChatId(nextChats[0].id);
      }

      return nextChats;
    });
  }

  async function handleSend(question) {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setError(null);

    const userMessage = { role: "user", content: trimmed };

    updateChat(activeChat.id, (chat) => ({
      ...chat,
      title: chat.messages.length === 0 ? trimmed.slice(0, 40) : chat.title,
      messages: [...chat.messages, userMessage],
    }));

    setLoading(true);

    try {
      const data = await askQuestion(trimmed);

      const assistantMessage = {
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };

      updateChat(activeChat.id, (chat) => ({
        ...chat,
        messages: [...chat.messages, assistantMessage],
      }));
    } catch (err) {
      setError(
        "Could not reach the assistant backend. Make sure the API server is running."
      );

      const assistantMessage = {
        role: "assistant",
        content:
          "Sorry, something went wrong while contacting the server. Please try again.",
        sources: [],
      };

      updateChat(activeChat.id, (chat) => ({
        ...chat,
        messages: [...chat.messages, assistantMessage],
      }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        chats={chats}
        activeChatId={activeChat.id}
        isOpen={sidebarOpen}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onClearChat={handleClearChat}
        onDeleteChat={handleDeleteChat}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="app-main">
        <Header onToggleSidebar={() => setSidebarOpen((open) => !open)} />

        {error && <div className="app-error-banner">{error}</div>}

        <ChatWindow
          messages={activeChat.messages}
          loading={loading}
          onExampleClick={handleSend}
        />

        <MessageInput onSend={handleSend} loading={loading} />
      </div>
    </div>
  );
}
