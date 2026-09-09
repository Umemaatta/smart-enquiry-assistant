import questCrest from "../assets/quest_crest.jpg";
import "../styles/Header.css";

export default function Header({ onToggleSidebar }) {
  return (
    <header className="app-header">
      <button
        className="sidebar-toggle-btn"
        onClick={onToggleSidebar}
        aria-label="Toggle sidebar"
      >
        <span />
        <span />
        <span />
      </button>

      <img src={questCrest} alt="QUEST Logo" className="header-logo" />

      <div className="header-university">
        <h1>Quaid-e-Awam University</h1>
        <p className="university-line-1">
          of Engineering, Science &amp; Technology
        </p>
        <p className="university-line-2">Nawabshah, Sindh, Pakistan</p>
      </div>
    </header>
  );
}
