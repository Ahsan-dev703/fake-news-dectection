import { useRef } from "react";
import { MdCloudUpload } from "react-icons/md";

const VALID_VIDEO_TYPES = [
  "video/mp4",
  "video/avi",
  "video/quicktime",
  "video/x-matroska",
];

const VideoAnalysis = ({
  onAnalyze,
  loading,
  onError,
  setFilePreview,
  setUploadedFile,
  uploadedFile,
}) => {
  const fileInputRef = useRef(null);

  const handleVideoSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!VALID_VIDEO_TYPES.includes(file.type)) {
      onError("Please select a valid stream container (MP4, AVI, MOV)");
      return;
    }

    setUploadedFile(file);
    onError("");

    setFilePreview({
      url: URL.createObjectURL(file),
      type: "video",
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + " MB",
    });
  };

  return (
    <div className="tab-content">
      <h2>Video Temporal Engine</h2>
      <p className="description">Process keyframe variance for verification</p>

      <div
        className="upload-area"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          onChange={handleVideoSelect}
          style={{ display: "none" }}
        />
        <div className="upload-prompt">
          <MdCloudUpload className="upload-icon" />
          <p>Click or Drop Video Asset</p>
          <p className="upload-hint">Max allocation: 500MB</p>
        </div>
      </div>

      <button
        className="predict-btn"
        onClick={onAnalyze}
        disabled={loading || !uploadedFile}
      >
        {loading ? "Processing Sequence..." : "Execute Temporal Verification"}
      </button>
    </div>
  );
};

export default VideoAnalysis;
