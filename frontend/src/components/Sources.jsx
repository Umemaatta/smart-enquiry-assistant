import { useState } from "react";
import "../styles/Sources.css";

export default function Sources({ sources }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources">
      <button
        className="sources-toggle"
        onClick={() => setExpanded((open) => !open)}
      >
        <span className={`sources-caret ${expanded ? "open" : ""}`}>▸</span>
        Sources ({sources.length})
      </button>

      {expanded && (
        <div className="sources-list">
          {sources.map((source, index) => (
            <div className="source-item" key={index}>
              <span className="source-doc">
                {source.document || "University document"}
              </span>
              {source.page && (
                <span className="source-page">Page {source.page}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
