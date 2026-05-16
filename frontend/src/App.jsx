import { useState } from "react";
import {
  MdTextFields,
  MdImage,
  MdVideoLibrary,
  MdOutlineScreenSearchDesktop,
  MdRemoveRedEye,
} from "react-icons/md";
import TextAnalysis from "./components/Tabs/TextAnalysis";
import ImageAnalysis from "./components/Tabs/ImageAnalysis";
import VideoAnalysis from "./components/Tabs/VideoAnalysis";
import AnalysisResults from "./components/Results/AnalysisResults";
import { apiService } from "./services/api";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("text");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filePreview, setFilePreview] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);

  const resetTabState = (tab) => {
    setActiveTab(tab);
    setResult(null);
    setError("");
    setFilePreview(null);
    setUploadedFile(null);
  };

  const handleTextAnalyze = async (textText) => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiService.analyzeText(textText);
      if (data.success) {
        setResult({
          type: "text",
          prediction: data.data.prediction,
          confidence: data.data.confidence,
          probabilities: data.data.probabilities,
        });
      } else {
        setError(data.error || "Prediction failed");
      }
    } catch (err) {
      setError("Error connecting to API. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleImageAnalyze = async () => {
    if (!uploadedFile) return setError("Please select an image file");
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiService.analyzeImage(uploadedFile);
      if (data.success) {
        setResult({
          type: "image",
          prediction: data.data.prediction.prediction,
          confidence: data.data.prediction.confidence,
          extractedText: data.data.ocr.extracted_text,
          ocrConfidence: data.data.ocr.confidence,
          manipulation: data.data.manipulation_analysis,
        });
      } else {
        setError(data.error || "Image analysis failed");
      }
    } catch (err) {
      setError("Error analyzing image. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleVideoAnalyze = async () => {
    if (!uploadedFile) return setError("Please select a video file");
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiService.analyzeVideo(uploadedFile);
      if (data.success) {
        setResult({
          type: "video",
          overallPrediction: data.data.summary.overall_prediction,
          confidence: data.data.summary.average_confidence,
          framesAnalyzed: data.data.frames_analyzed,
          fakeFrames: data.data.summary.fake_frames,
          realFrames: data.data.summary.real_frames,
          recommendation: data.data.summary.recommendation,
          framePredictions: data.data.frame_predictions,
          extractedContent: data.data.extracted_content_preview,
        });
      } else {
        setError(data.error || "Video analysis failed");
      }
    } catch (err) {
      setError("Error analyzing video. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-container">
      {/* HEADER SECTION */}
      <div className="title-section">
        <h1 className="designByAhsan">
          Fake News Detection System
        </h1>
        <p className="subtitle">
          Advanced Neural Network Analysis for Text, Images & Videos
        </p>
      </div>

      {/* DASHBOARD WORKSPACE GRID */}
      <div className="workspace-grid">
        {/* COLUMN 1: CONTROLS & SUBMISSIONS */}
        <div className="control-panel">
          <div>
            <div className="tab-navigation">
              {["text", "image", "video"].map((tab) => (
                <button
                  key={tab}
                  className={`tab-btn ${activeTab === tab ? "active" : ""}`}
                  onClick={() => resetTabState(tab)}
                >
                  {tab === "text" && (
                    <>
                      <MdTextFields /> Text
                    </>
                  )}
                  {tab === "image" && (
                    <>
                      <MdImage /> Image
                    </>
                  )}
                  {tab === "video" && (
                    <>
                      <MdVideoLibrary /> Video
                    </>
                  )}
                </button>
              ))}
            </div>

            {error && (
              <div className="error-message">
                <span>⚠️ {error}</span>
              </div>
            )}

            {activeTab === "text" && (
              <TextAnalysis onAnalyze={handleTextAnalyze} loading={loading} />
            )}
            {activeTab === "image" && (
              <ImageAnalysis
                onAnalyze={handleImageAnalyze}
                loading={loading}
                onError={setError}
                setFilePreview={setFilePreview}
                setUploadedFile={setUploadedFile}
                uploadedFile={uploadedFile}
              />
            )}
            {activeTab === "video" && (
              <VideoAnalysis
                onAnalyze={handleVideoAnalyze}
                loading={loading}
                onError={setError}
                setFilePreview={setFilePreview}
                setUploadedFile={setUploadedFile}
                uploadedFile={uploadedFile}
              />
            )}
          </div>

          {loading && (
            <div className="loader-container">
              <div className="pulse-ring"></div>
              <p className="subtitle">Processing Neural Pipelines...</p>
            </div>
          )}
        </div>

        {/* COLUMN 2: REAL-TIME ISOLATED PREVIEW PANEL */}
        <div className="preview-panel">
          {filePreview ? (
            <>
              {filePreview.type === "image" ? (
                <img
                  src={filePreview.url}
                  alt="Source Matrix Preview"
                  className="image-preview-frame"
                />
              ) : (
                <div className="video-preview-card">
                  <MdVideoLibrary
                    size={48}
                    style={{ color: "var(--accent-color)" }}
                  />
                  <p className="file-name-meta">{filePreview.name}</p>
                  <p className="subtitle">{filePreview.size}</p>
                </div>
              )}
            </>
          ) : (
            <div className="preview-placeholder">
              <MdRemoveRedEye size={36} />
              <p>Real-time file preview viewport</p>
              <p className="subtitle" style={{ fontSize: "0.75rem" }}>
                {activeTab === "text"
                  ? "Linguistic analysis needs no media track"
                  : "Awaiting stream input..."}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* DETACHED COMPONENT MODAL SYSTEM */}
      <AnalysisResults result={result} onClose={() => setResult(null)} />
    </div>
  );
}

export default App;
