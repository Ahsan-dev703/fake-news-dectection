import { MdClose, MdAssessment } from "react-icons/md";

const AnalysisResults = ({ result, onClose }) => {
  if (!result) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      {/* StopPropagation prevents clicking internal elements from closing modal */}
      <div className="result-card" onClick={(e) => e.stopPropagation()}>
        <button
          className="close-btn"
          onClick={onClose}
          aria-label="Close popup"
        >
          <MdClose size={20} />
        </button>

        <h3>
          <MdAssessment className="title-icon" />
          Analysis Diagnosis
        </h3>

        {result.type === "text" && (
          <>
            <div className={`result-verdict ${result.prediction}`}>
              {result.prediction}
            </div>
            <div className="result-details">
              <div className="detail">
                <strong>Confidence Score</strong>
                <p>{(result.confidence * 100).toFixed(2)}%</p>
              </div>
              {result.probabilities && (
                <div className="detail">
                  <strong>Distribution Weights</strong>
                  <p>
                    Fake: {(result.probabilities.fake * 100).toFixed(2)}% |
                    Real: {(result.probabilities.real * 100).toFixed(2)}%
                  </p>
                </div>
              )}
            </div>
          </>
        )}

        {result.type === "image" && (
          <>
            <div className={`result-verdict ${result.prediction}`}>
              {result.prediction}
            </div>
            <div className="result-details">
              <div className="detail">
                <strong>Model Confidence</strong>
                <p>
                  {(result.confidence * 100).toFixed(2)}% (OCR:{" "}
                  {(result.ocrConfidence * 100).toFixed(2)}%)
                </p>
              </div>
              {result.extractedText && (
                <div className="detail">
                  <strong>Extracted Text Metadata</strong>
                  <p className="extracted-text">{result.extractedText}</p>
                </div>
              )}
              {result.manipulation && (
                <div className="detail">
                  <strong>Structural Inconsistency Analysis</strong>
                  <p>{result.manipulation.interpretation}</p>
                </div>
              )}
            </div>
          </>
        )}

        {result.type === "video" && (
          <>
            <div className={`result-verdict ${result.overallPrediction}`}>
              {result.overallPrediction}
            </div>
            <div className="result-details">
              <div className="detail">
                <strong>Frame Analysis Array</strong>
                <p>
                  Total Evaluated: {result.framesAnalyzed} (Real:{" "}
                  {result.realFrames} / Manipulated: {result.fakeFrames})
                </p>
              </div>
              <div className="detail">
                <strong>Mean Sequence Confidence</strong>
                <p>{(result.confidence * 100).toFixed(2)}%</p>
              </div>
              <div className="detail">
                <strong>Automated Safety Recommendation</strong>
                <p>{result.recommendation}</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AnalysisResults;
