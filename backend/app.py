"""
Fake News Detection API - Multimodal
Supports text, image, and video analysis
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import configuration
from config import get_config, Config

# Import services
from services import PredictionService, OCRService, ImageService, VideoService

# Import utilities
from utils import FileValidator, TextPreprocessor, ErrorHandler, ErrorCodes

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Setup CORS
CORS(app, origins=config.CORS_ORIGINS.split(",") if config.CORS_ORIGINS != "*" else "*")

# Create uploads directory
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)


@app.before_request
def initialize_services():
    """Initialize services on first request"""
    global services_initialized

    if not hasattr(app, "services_initialized"):
        logger.info("Initializing services...")

        # Initialize prediction service (model + vectorizer)
        success, msg = PredictionService.initialize(config.MODEL_PATH)
        if not success:
            logger.error(f"Failed to initialize PredictionService: {msg}")
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.MODEL_NOT_FOUND,
                        "Model failed to load. Please check model file.",
                    )
                ),
                500,
            )

        # Initialize OCR service
        try:
            OCRService.initialize(config.OCR_LANGUAGES)
        except Exception as e:
            logger.warning(f"OCR service initialization failed: {str(e)}")
            # Continue anyway, OCR will fail gracefully

        app.services_initialized = True
        logger.info("All services initialized successfully")


# ============================================================================
# HEALTH CHECK & INFO ENDPOINTS
# ============================================================================


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "API Running",
            "version": "2.0",
            "modes": ["text", "image", "video"],
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/health", methods=["GET"])
def health():
    """Detailed health check"""
    model_info = PredictionService.get_model_info()
    return jsonify(
        {
            "status": "healthy",
            "model": model_info,
            "services": {
                "prediction": model_info.get("loaded", False),
                "ocr": True,  # We'll check this dynamically
                "image_processing": True,
                "video_processing": True,
            },
        }
    )


@app.route("/api/v1/info", methods=["GET"])
def get_info():
    """Get API and model information"""
    return jsonify(
        {
            "api_version": "2.0",
            "supported_modes": ["text", "image", "video"],
            "model_info": PredictionService.get_model_info(),
            "config": {
                "max_image_size": config.MAX_IMAGE_SIZE,
                "max_video_size": config.MAX_VIDEO_SIZE,
                "allowed_image_extensions": list(config.ALLOWED_IMAGE_EXTENSIONS),
                "allowed_video_extensions": list(config.ALLOWED_VIDEO_EXTENSIONS),
            },
        }
    )


# ============================================================================
# TEXT ANALYSIS ENDPOINTS
# ============================================================================


@app.route("/predict", methods=["POST"])
def predict_text():
    """
    Original text prediction endpoint (kept for backward compatibility)

    Request: {"text": "news text here"}
    Response: {"prediction": "Real News" | "Fake News", "confidence": 0.95}
    """
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "Missing 'text' field in request"
                    )
                ),
                400,
            )

        text = data.get("text", "").strip()

        if not text:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "Text cannot be empty"
                    )
                ),
                400,
            )

        # Predict
        result = PredictionService.predict(text)

        if not result.get("success"):
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.PREDICTION_FAILED,
                        result.get("error", "Prediction failed"),
                    )
                ),
                500,
            )

        return jsonify(
            ErrorHandler.format_success_response(
                {
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "prediction": result["prediction"],
                    "confidence": result["confidence"],
                    "probabilities": result.get("probabilities"),
                },
                "Text analysis completed",
            )
        )

    except Exception as e:
        logger.error(f"Text prediction error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


@app.route("/api/v1/text/predict", methods=["POST"])
def predict_text_v2():
    """
    Enhanced text prediction endpoint with batch support

    Request: {"text": "news text"} or {"texts": ["text1", "text2"]}
    """
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "Missing request body"
                    )
                ),
                400,
            )

        # Handle batch prediction
        if "texts" in data:
            texts = data.get("texts", [])
            if not isinstance(texts, list):
                return (
                    jsonify(
                        ErrorHandler.format_error_response(
                            ErrorCodes.INVALID_FILE, "texts must be a list"
                        )
                    ),
                    400,
                )

            result = PredictionService.predict_batch(texts)

            if not result.get("success"):
                return (
                    jsonify(
                        ErrorHandler.format_error_response(
                            ErrorCodes.PREDICTION_FAILED, result.get("error")
                        )
                    ),
                    500,
                )

            return jsonify(
                ErrorHandler.format_success_response(
                    result.get("results", []),
                    f"Batch prediction completed for {result.get('count', 0)} texts",
                )
            )

        # Handle single prediction
        elif "text" in data:
            text = data.get("text", "").strip()

            if not text:
                return (
                    jsonify(
                        ErrorHandler.format_error_response(
                            ErrorCodes.INVALID_FILE, "Text cannot be empty"
                        )
                    ),
                    400,
                )

            result = PredictionService.predict(text)

            if not result.get("success"):
                return (
                    jsonify(
                        ErrorHandler.format_error_response(
                            ErrorCodes.PREDICTION_FAILED, result.get("error")
                        )
                    ),
                    500,
                )

            return jsonify(
                ErrorHandler.format_success_response(
                    {
                        "text_preview": text[:100] + "...",
                        "prediction": result["prediction"],
                        "confidence": result["confidence"],
                        "probabilities": result.get("probabilities"),
                    },
                    "Text analysis completed",
                )
            )

        else:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE,
                        "Request must contain 'text' or 'texts' field",
                    )
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Text prediction error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


# ============================================================================
# IMAGE ANALYSIS ENDPOINTS
# ============================================================================


@app.route("/api/v1/image/upload", methods=["POST"])
def upload_image():
    """
    Analyze image and extract text with fake news prediction

    Request: multipart/form-data with 'file' field
    Response: {"prediction": "Real News", "confidence": 0.95, "extracted_text": "..."}
    """
    try:
        # Check if file is in request
        if "file" not in request.files:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE,
                        "No file provided. Use 'file' field in multipart form",
                    )
                ),
                400,
            )

        file = request.files["file"]

        if file.filename == "":
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file selected"
                    )
                ),
                400,
            )

        # Validate image
        is_valid, error_msg = FileValidator.validate_image(file, file.filename)
        if not is_valid:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, error_msg
                    )
                ),
                400,
            )

        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + file.filename
        filepath = FileValidator.save_file(file, config.UPLOAD_FOLDER, filename)

        logger.info(f"Image uploaded: {filepath}")

        # Get image info
        img_info = ImageService.get_image_info(filepath)

        # Extract text using OCR
        ocr_result = OCRService.extract_text(filepath, config.OCR_CONFIDENCE_THRESHOLD)

        if not ocr_result.get("success"):
            logger.warning(f"OCR failed for image: {ocr_result.get('error')}")
            # Continue even if OCR fails
            extracted_text = ""
            ocr_confidence = 0.0
        else:
            extracted_text = ocr_result.get("text", "")
            ocr_confidence = ocr_result.get("confidence", 0.0)

        # Predict using extracted text
        if extracted_text.strip():
            prediction = PredictionService.predict(extracted_text)
        else:
            prediction = {
                "success": False,
                "error": "No text extracted from image",
                "prediction": "Unable to analyze",
                "confidence": 0.0,
            }

        # Detect image manipulation (optional)
        manipulation_result = ImageService.detect_image_manipulation(filepath)

        # Cleanup - optionally delete the uploaded file
        # os.remove(filepath)

        response_data = {
            "file_name": filename,
            "image_info": img_info if img_info.get("success") else None,
            "ocr": {
                "success": ocr_result.get("success"),
                "extracted_text": extracted_text,
                "confidence": ocr_confidence,
                "text_count": ocr_result.get("text_count", 0),
            },
            "prediction": {
                "success": prediction.get("success"),
                "prediction": prediction.get("prediction"),
                "confidence": prediction.get("confidence"),
                "probabilities": prediction.get("probabilities"),
            },
            "manipulation_analysis": (
                manipulation_result if manipulation_result.get("success") else None
            ),
        }

        return jsonify(
            ErrorHandler.format_success_response(
                response_data, "Image analysis completed"
            )
        )

    except Exception as e:
        logger.error(f"Image upload error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


@app.route("/api/v1/image/ocr", methods=["POST"])
def extract_text_from_image():
    """
    Extract text from image using OCR only (without fake news prediction)

    Request: multipart/form-data with 'file' field
    Response: {"extracted_text": "...", "confidence": 0.95}
    """
    try:
        if "file" not in request.files:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file provided"
                    )
                ),
                400,
            )

        file = request.files["file"]

        if file.filename == "":
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file selected"
                    )
                ),
                400,
            )

        # Validate and save
        is_valid, error_msg = FileValidator.validate_image(file, file.filename)
        if not is_valid:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, error_msg
                    )
                ),
                400,
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + file.filename
        filepath = FileValidator.save_file(file, config.UPLOAD_FOLDER, filename)

        # Extract text
        ocr_result = OCRService.extract_text(filepath, config.OCR_CONFIDENCE_THRESHOLD)

        # Cleanup
        # os.remove(filepath)

        if not ocr_result.get("success"):
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.OCR_FAILED, ocr_result.get("error")
                    )
                ),
                500,
            )

        return jsonify(
            ErrorHandler.format_success_response(
                {
                    "file_name": filename,
                    "extracted_text": ocr_result.get("text"),
                    "confidence": ocr_result.get("confidence"),
                    "text_count": ocr_result.get("text_count"),
                    "raw_results": ocr_result.get("raw_results", [])[
                        :10
                    ],  # Top 10 only
                },
                "OCR extraction completed",
            )
        )

    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


# ============================================================================
# VIDEO ANALYSIS ENDPOINTS
# ============================================================================


@app.route("/api/v1/video/upload", methods=["POST"])
def upload_video():
    """
    Analyze video: extract frames, text, and predict fake news

    Request: multipart/form-data with 'file' field
    Response: {"predictions": [...], "summary": {...}}
    """
    try:
        if "file" not in request.files:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file provided"
                    )
                ),
                400,
            )

        file = request.files["file"]

        if file.filename == "":
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file selected"
                    )
                ),
                400,
            )

        # Validate video
        is_valid, error_msg = FileValidator.validate_video(file, file.filename)
        if not is_valid:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, error_msg
                    )
                ),
                400,
            )

        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + file.filename
        filepath = FileValidator.save_file(file, config.UPLOAD_FOLDER, filename)

        logger.info(f"Video uploaded: {filepath}")

        # Get video info
        video_info = VideoService.get_video_info(filepath)

        if not video_info.get("success"):
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.VIDEO_PROCESSING_FAILED, video_info.get("error")
                    )
                ),
                400,
            )

        # Extract frames
        success, frame_paths, metadata = VideoService.extract_frames(
            filepath,
            sample_rate=config.VIDEO_SAMPLE_RATE,
            max_frames=config.VIDEO_MAX_FRAMES,
            target_height=config.VIDEO_RESIZE_HEIGHT,
        )

        if not success:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.VIDEO_PROCESSING_FAILED, metadata.get("error")
                    )
                ),
                500,
            )

        # Extract text from frames and predict
        frame_predictions = []
        all_texts = []

        for idx, frame_path in enumerate(frame_paths):
            try:
                # OCR on frame
                ocr_result = OCRService.extract_text(
                    frame_path, config.OCR_CONFIDENCE_THRESHOLD
                )

                if ocr_result.get("success") and ocr_result.get("text"):
                    text = ocr_result.get("text", "")
                    all_texts.append(text)

                    # Predict
                    pred = PredictionService.predict(text)

                    frame_predictions.append(
                        {
                            "frame_index": idx,
                            "extracted_text": (
                                text[:100] + "..." if len(text) > 100 else text
                            ),
                            "ocr_confidence": ocr_result.get("confidence"),
                            "prediction": pred.get("prediction"),
                            "confidence": pred.get("confidence"),
                            "probabilities": pred.get("probabilities"),
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to process frame {idx}: {str(e)}")
                continue

        # Calculate summary
        if frame_predictions:
            fake_count = sum(
                1 for p in frame_predictions if p["prediction"] == "Fake News"
            )
            real_count = sum(
                1 for p in frame_predictions if p["prediction"] == "Real News"
            )
            avg_confidence = sum(p["confidence"] for p in frame_predictions) / len(
                frame_predictions
            )

            overall_prediction = (
                "Fake News" if fake_count >= real_count else "Real News"
            )
        else:
            fake_count = 0
            real_count = 0
            avg_confidence = 0.0
            overall_prediction = "Unable to analyze"

        # Cleanup frames
        VideoService.cleanup_frames(metadata.get("frames_dir"))

        # Optionally cleanup video file
        # os.remove(filepath)

        response_data = {
            "file_name": filename,
            "video_info": video_info,
            "frames_analyzed": len(frame_predictions),
            "frame_predictions": frame_predictions[:5],  # Top 5 frames in response
            "summary": {
                "overall_prediction": overall_prediction,
                "fake_frames": fake_count,
                "real_frames": real_count,
                "average_confidence": round(avg_confidence, 4),
                "recommendation": f"{fake_count} frames predicted as FAKE out of {len(frame_predictions)} analyzed",
            },
            "extracted_content_preview": " ".join(all_texts[:2])[:200] + "...",
        }

        return jsonify(
            ErrorHandler.format_success_response(
                response_data, "Video analysis completed"
            )
        )

    except Exception as e:
        logger.error(f"Video upload error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


@app.route("/api/v1/video/frames", methods=["POST"])
def extract_video_frames():
    """
    Extract frames from video without analysis (for preview)

    Request: multipart/form-data with 'file' field
    Response: {"frames_count": 10, "extracted_frames": [...]}
    """
    try:
        if "file" not in request.files:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file provided"
                    )
                ),
                400,
            )

        file = request.files["file"]

        if file.filename == "":
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "No file selected"
                    )
                ),
                400,
            )

        # Validate and save
        is_valid, error_msg = FileValidator.validate_video(file, file.filename)
        if not is_valid:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, error_msg
                    )
                ),
                400,
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + file.filename
        filepath = FileValidator.save_file(file, config.UPLOAD_FOLDER, filename)

        # Extract frames
        success, frame_paths, metadata = VideoService.extract_frames(
            filepath, sample_rate=5, max_frames=10
        )

        if not success:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.VIDEO_PROCESSING_FAILED, metadata.get("error")
                    )
                ),
                500,
            )

        # Cleanup
        VideoService.cleanup_frames(metadata.get("frames_dir"))

        return jsonify(
            ErrorHandler.format_success_response(
                {
                    "file_name": filename,
                    "total_frames_extracted": len(frame_paths),
                    "video_metadata": metadata,
                },
                "Frame extraction completed",
            )
        )

    except Exception as e:
        logger.error(f"Frame extraction error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.errorhandler(400)
def bad_request(error):
    return (
        jsonify(
            ErrorHandler.format_error_response(ErrorCodes.INVALID_FILE, "Bad request")
        ),
        400,
    )


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify(
            ErrorHandler.format_error_response(
                ErrorCodes.INTERNAL_ERROR, "Endpoint not found"
            )
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error):
    return (
        jsonify(
            ErrorHandler.format_error_response(
                ErrorCodes.INTERNAL_ERROR, "Internal server error"
            )
        ),
        500,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
