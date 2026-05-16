import { useState } from "react";

const TextAnalysis = ({ onAnalyze, loading }) => {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    if (text.trim()) onAnalyze(text);
  };

  return (
    <div className="tab-content">
      <h2>Text-Based Analysis</h2>
      <p className="description">Paste news text for direct analysis</p>

      <div className="input-wrapper">
        <textarea
          className="ai-textarea"
          placeholder="Paste news content here for linguistic analysis..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading}
        />
      </div>

      <button
        className="predict-btn "
        style={{marginTop:"1rem"}}
        onClick={handleSubmit}
        disabled={loading || !text.trim()}
      >
        {loading ? "Analyzing..." : "Analyze Text"}
      </button>
    </div>
  );
};

export default TextAnalysis;
