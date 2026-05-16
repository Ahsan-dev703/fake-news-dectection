import { useState } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const predictNews = async () => {
    if (!text.trim()) return;

    setLoading(true);
    setResult("");

    try {
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      setResult(data.prediction);
    } catch (error) {
      console.error("Error fetching prediction:", error);
      setResult("Error connecting to AI server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-container">
      <div className="title-section">
        <h1>Verify Intelligence</h1>
        <p className="subtitle">Neural Network Analysis for Truth Detection</p>
      </div>

      <div className="input-wrapper">
        <textarea
          className="ai-textarea"
          placeholder="Paste news content here for linguistic analysis..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>

      <button
        className="predict-btn"
        onClick={predictNews}
        disabled={loading || !text}
      >
        {loading ? "Analyzing Patterns..." : "Run AI Diagnostics"}
      </button>

      {loading && (
        <div className="loader-container">
          <div className="pulse-ring"></div>
          <p className="subtitle">Scanning for discrepancies...</p>
        </div>
      )}

      {result && (
        <div className="result-card">
          <span className="subtitle">Verdict:</span>
          <div className={`result-text ${result}`}>{result}</div>
        </div>
      )}
    </div>
  );
}

export default App;
