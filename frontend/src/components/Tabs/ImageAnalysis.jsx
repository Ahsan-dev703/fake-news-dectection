import { useRef } from "react";
import { MdCloudUpload } from "react-icons/md";

const VALID_IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/bmp",
  "image/webp",
];

const ImageAnalysis = ({
  onAnalyze,
  loading,
  onError,
  setFilePreview,
  setUploadedFile,
  uploadedFile,
}) => {
  const fileInputRef = useRef(null);

  const handleImageSelect = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!VALID_IMAGE_TYPES.includes(file.type)) {
      onError("Please select a valid image file (JPG, PNG, WEBP)");
      return;
    }

    setUploadedFile(file);
    onError("");

    const reader = new FileReader();
    reader.onload = (e) => {
      setFilePreview({
        url: e.target.result,
        type: "image",
        name: file.name,
      });
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="tab-content">
      <h2>Image Engine</h2>
      <p className="description">
        Upload imagery asset to evaluate pixel manipulation
      </p>

      <div
        className="upload-area"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageSelect}
          style={{ display: "none" }}
        />
        <div className="upload-prompt">
          <MdCloudUpload className="upload-icon" />
          <p>Click or Drop Image File</p>
          <p className="upload-hint">Max allocation: 50MB</p>
        </div>
      </div>

      <button
        className="predict-btn"
        onClick={onAnalyze}
        disabled={loading || !uploadedFile}
      >
        {loading ? "Computing Core Analysis..." : "Execute Image Verification"}
      </button>
    </div>
  );
};

export default ImageAnalysis;
