import "../styles/WelcomeScreen.css";

const EXAMPLE_QUESTIONS = [
  "What is the minimum percentage required for Engineering programs?",
  "How is the merit calculated?",
  "What is the fee for B.E programs?",
  "Is Pre-Medical eligible for Artificial Intelligence?",
];

export default function WelcomeScreen({ onExampleClick }) {
  return (
    <div className="welcome-screen">
      <p className="welcome-brand">Smart Enquiry Assistant</p>
      <h2>How can I help you?</h2>
      <p className="welcome-desc">
        Ask questions about QUEST admissions, programs, fees, eligibility,
        rules and other official university information.
      </p>

      <div className="welcome-examples">
        {EXAMPLE_QUESTIONS.map((question) => (
          <button
            key={question}
            className="welcome-example-chip"
            onClick={() => onExampleClick(question)}
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
