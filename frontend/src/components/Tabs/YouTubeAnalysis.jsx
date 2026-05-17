import { useState } from "react";

const YouTubeAnalysis = ({ onAnalyze, loading, onError, setFilePreview }) => {
  const [url, setUrl] = useState("");
  const [cookiesText, setCookiesText] = useState("");

  const handleSubmit = () => {
    if (!url || (!url.includes("youtube.com") && !url.includes("youtu.be"))) {
      onError("Please enter a valid YouTube URL");
      return;
    }
    onError("");
    onAnalyze(url, cookiesText || null);
    // preview thumbnail could be fetched from backend later
    setFilePreview({ url: null, type: "youtube", name: url });
  };

  return (
    <div className="tab-content">
      <h2>YouTube URL Analysis</h2>
      <p className="description">
        Paste a YouTube link to analyze the video content
      </p>

      <input
        type="text"
        placeholder="https://www.youtube.com/watch?v=..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={{ width: "100%", padding: "8px", marginBottom: "12px" }}
      />

      <textarea
        placeholder="Optional: paste cookies.txt content here if YouTube requires authentication"
        value={cookiesText}
        onChange={(e) => setCookiesText(e.target.value)}
        rows={4}
        style={{
          width: "100%",
          padding: "8px",
          marginBottom: "12px",
          fontSize: "0.85rem",
        }}
      />

      <button
        className="predict-btn"
        onClick={handleSubmit}
        disabled={loading || !url}
      >
        {loading ? "Processing YouTube..." : "Analyze YouTube URL"}
      </button>
    </div>
  );
};

export default YouTubeAnalysis;
