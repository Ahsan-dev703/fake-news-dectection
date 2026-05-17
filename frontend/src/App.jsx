import { useState } from "react";
import { FaYoutube } from "react-icons/fa";
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
import YouTubeAnalysis from "./components/Tabs/YouTubeAnalysis";
import AnalysisResults from "./components/Results/AnalysisResults";
import { apiService } from "./services/api";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState("text");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [currentJobId, setCurrentJobId] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
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
      setUploadProgress(0);
      const data = await apiService.analyzeImage(uploadedFile, {
        quality: 0.8,
        onProgress: (p) => setUploadProgress(p),
      });
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
      setUploadProgress(0);
    }
  };

  const handleVideoAnalyze = async () => {
    if (!uploadedFile) return setError("Please select a video file");
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setUploadProgress(0);
      const data = await apiService.analyzeVideo(uploadedFile, {
        onProgress: (p) => setUploadProgress(p),
        async: false,
      });
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
      setUploadProgress(0);
    }
  };

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const checkJobStatus = async (jobId) => {
    if (!jobId) return setError("No job id available to check");
    setLoading(true);
    setError("");
    try {
      const poll = await apiService.pollJob(jobId);
      if (!poll.success)
        return setError(poll.error || "Failed to fetch job status");

      if (poll.data.status === "finished") {
        const jobResult = poll.data.result;
        if (jobResult && jobResult.summary) {
          setResult({
            type: "video",
            overallPrediction: jobResult.summary.overall_prediction,
            confidence: jobResult.summary.average_confidence,
            framesAnalyzed: jobResult.frames_analyzed,
            fakeFrames: jobResult.summary.fake_frames,
            realFrames: jobResult.summary.real_frames,
            recommendation:
              jobResult.summary.recommendation ||
              (jobResult.summary.overall_prediction === "Fake News"
                ? "Use caution: this video may contain false or misleading information."
                : jobResult.summary.overall_prediction === "Real News"
                  ? "This video appears genuine based on the extracted text."
                  : "Insufficient text was found for a reliable verdict."),
            framePredictions: jobResult.frame_predictions,
            extractedContent: jobResult.video_metadata,
          });
          setStatusMsg("");
          setCurrentJobId(null);
          return;
        }
        return setError("Job finished but no analysis result found");
      }

      // not finished yet
      setStatusMsg(`Job ${jobId} status: ${poll.data.status}`);
    } catch (err) {
      setError(err.message || "Error checking job status");
    } finally {
      setLoading(false);
    }
  };

  const handleYouTubeAnalyze = async (url, cookies = null) => {
    if (!url) return setError("Please provide a YouTube URL");
    setLoading(true);
    setError("");
    setResult(null);
    setStatusMsg("");
    setCurrentJobId(null);

    try {
      console.log("[YouTube] Sending request to backend...");
      const data = await apiService.analyzeYouTube(url, {
        async: true,
        cookies,
      });

      console.log("[YouTube] Response:", data);

      if (!data.success) {
        setError(data.error || "YouTube analysis failed");
        setLoading(false);
        return;
      }

      // FAST PATH: Quick analysis (captions available)
      if (data.data && data.data.prediction && !data.data.job_id) {
        console.log("[YouTube] FAST PATH: Using captions");
        setLoading(false);
        setResult({
          type: "text",
          prediction: data.data.prediction.prediction,
          confidence: data.data.prediction.confidence,
          probabilities: data.data.prediction.probabilities,
          transcript: data.data.transcript || null,
          videoMetadata: data.data.video_metadata,
          transcriptSource: "captions",
        });
        return;
      }

      // SLOW PATH: Background job processing
      if (data.data && data.data.job_id) {
        const jobId = data.data.job_id;
        console.log("[YouTube] SLOW PATH: Job queued - " + jobId);
        setCurrentJobId(jobId);
        setStatusMsg(`Video processing started (Job: ${jobId})`);

        let pollingAttempts = 0;
        const maxPollingAttempts = 180; // 30 minutes with exponential backoff
        let pollIntervalMs = 1000; // Start with 1 second
        const maxPollIntervalMs = 10000; // Cap at 10 seconds

        // Poll loop
        while (pollingAttempts < maxPollingAttempts) {
          pollingAttempts++;

          // Wait before polling
          await wait(pollIntervalMs);

          console.log(
            `[YouTube] Poll attempt ${pollingAttempts}: Status check...`,
          );

          try {
            const pollResponse = await apiService.pollJob(jobId);
            console.log("[YouTube] Poll response:", pollResponse);

            if (!pollResponse.success) {
              console.error("[YouTube] Poll failed:", pollResponse.error);
              setError(
                `Failed to check job status: ${pollResponse.error || "Unknown error"}`,
              );
              setStatusMsg("");
              setCurrentJobId(null);
              setLoading(false);
              return;
            }

            const jobStatus = pollResponse.data.status;
            const jobResult = pollResponse.data.result;
            const progressMsg = pollResponse.data.progress_message || "";

            console.log(
              `[YouTube] Job status: ${jobStatus}, Progress: ${progressMsg}`,
            );

            // Update UI with current status
            if (progressMsg) {
              setStatusMsg(
                `Processing: ${progressMsg} (Attempt: ${pollingAttempts}/${maxPollingAttempts})`,
              );
            } else {
              setStatusMsg(
                `Processing: ${jobStatus}... (Attempt: ${pollingAttempts}/${maxPollingAttempts})`,
              );
            }

            // Job finished successfully
            if (jobStatus === "finished") {
              console.log("[YouTube] Job FINISHED with result:", jobResult);

              if (jobResult && jobResult.summary) {
                setLoading(false);
                setStatusMsg("");
                setCurrentJobId(null);

                setResult({
                  type: "video",
                  overallPrediction: jobResult.summary.overall_prediction,
                  confidence: jobResult.summary.average_confidence,
                  framesAnalyzed: jobResult.frames_analyzed,
                  fakeFrames: jobResult.summary.fake_frames,
                  realFrames: jobResult.summary.real_frames,
                  recommendation: jobResult.summary.recommendation,
                  framePredictions: jobResult.frame_predictions,
                  extractedContent: jobResult.video_metadata,
                });
                return;
              } else if (jobResult && jobResult.error_type) {
                // Finished but no text detected or other non-fatal error
                setLoading(false);
                setStatusMsg("");
                setCurrentJobId(null);

                setResult({
                  type: "video",
                  overallPrediction:
                    jobResult.summary?.overall_prediction ||
                    "Unable to analyze",
                  confidence: jobResult.summary?.average_confidence || 0,
                  framesAnalyzed: jobResult.frames_analyzed || 0,
                  fakeFrames: jobResult.summary?.fake_frames || 0,
                  realFrames: jobResult.summary?.real_frames || 0,
                  recommendation:
                    jobResult.summary?.recommendation || "Insufficient data",
                  framePredictions: jobResult.frame_predictions || [],
                  extractedContent: jobResult.video_metadata,
                });
                return;
              }

              setError("Job completed but no valid result structure received");
              setLoading(false);
              setStatusMsg("");
              setCurrentJobId(null);
              return;
            }

            // Job encountered an error
            if (jobStatus === "error") {
              console.error("[YouTube] Job ERROR:", jobResult);
              const errorMessage =
                jobResult?.error ||
                pollResponse.data.error ||
                "Video processing failed";
              setError(`Processing error: ${errorMessage}`);
              setStatusMsg("");
              setCurrentJobId(null);
              setLoading(false);
              return;
            }

            // Still processing - increase poll interval (exponential backoff)
            pollIntervalMs = Math.min(pollIntervalMs * 1.3, maxPollIntervalMs);
          } catch (pollError) {
            console.error("[YouTube] Poll error:", pollError);
            setError(`Error checking job status: ${pollError.message}`);
            setStatusMsg("");
            setCurrentJobId(null);
            setLoading(false);
            return;
          }
        }

        // Timeout - job took too long
        console.error(
          "[YouTube] Job polling TIMEOUT after " +
            pollingAttempts +
            " attempts",
        );
        setError(
          `Video processing timeout. Job may still be processing in the background. Job ID: ${jobId}`,
        );
        setStatusMsg("");
        setCurrentJobId(null);
        setLoading(false);
        return;
      }

      // No result and no job_id - unexpected response structure
      console.error("[YouTube] Unexpected response structure:", data.data);
      setError(
        "Server returned unexpected response. Please try again or contact support.",
      );
      setLoading(false);
      return;
    } catch (err) {
      console.error("[YouTube] Exception:", err);
      setError(
        err.message ||
          "Error analyzing YouTube URL. Ensure backend is running.",
      );
      setLoading(false);
    }
  };

  return (
    <div className="ai-container">
      {/* HEADER SECTION */}
      <div className="title-section">
        <h1 className="designByAhsan">Fake News Detection System</h1>
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
              {["text", "image", "video", "youtube"].map((tab) => (
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
                  {/* YouTube Condition Added */}
                  {tab === "youtube" && (
                    <>
                      <FaYoutube /> YouTube
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
            {statusMsg && (
              <div
                className="status-message"
                style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}
              >
                <span>ℹ️ {statusMsg}</span>
                {currentJobId && (
                  <button
                    className="small-btn"
                    onClick={() => checkJobStatus(currentJobId)}
                  >
                    Check status
                  </button>
                )}
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
            {activeTab === "youtube" && (
              <YouTubeAnalysis
                onAnalyze={handleYouTubeAnalyze}
                loading={loading}
                onError={setError}
                setFilePreview={setFilePreview}
              />
            )}
          </div>

          {loading && (
            <div className="loader-container">
              <div className="pulse-ring"></div>
              <p className="subtitle">
                {uploadProgress > 0 && uploadProgress < 1
                  ? `Uploading... ${Math.round(uploadProgress * 100)}%`
                  : "Processing Neural Pipelines..."}
              </p>
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
