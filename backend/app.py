"""
Fake News Detection API - Multimodal
Supports text, image, and video analysis
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import tempfile
from flask_cors import CORS
import concurrent.futures
import uuid
import time
import threading

# Ensure backend directory is on sys.path so imports work whether this file is run directly
# or imported via Flask / module mode.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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

# Background executor for heavy tasks
app.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


# Thread-safe job store with lock
class ThreadSafeJobStore:
    """Thread-safe in-memory job store with locking mechanism"""

    def __init__(self):
        self._store = {}
        self._lock = threading.RLock()

    def get(self, job_id):
        with self._lock:
            return self._store.get(job_id)

    def set(self, job_id, value):
        with self._lock:
            self._store[job_id] = value

    def update(self, job_id, updates):
        with self._lock:
            if job_id in self._store:
                self._store[job_id].update(updates)

    def exists(self, job_id):
        with self._lock:
            return job_id in self._store


app.job_store = ThreadSafeJobStore()


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

        # Optionally run async background job when requested via ?async=true
        run_async = request.args.get("async", "false").lower() == "true"

        def process_video_job(fp, fname):
            job_result = {
                "file_name": fname,
                "video_info": None,
                "frames_analyzed": 0,
                "frame_predictions": [],
                "summary": {},
                "extracted_content_preview": "",
            }

            video_info = VideoService.get_video_info(fp)
            job_result["video_info"] = video_info

            if not video_info.get("success"):
                job_result["error"] = video_info.get("error")
                return job_result

            success, frame_paths, metadata = VideoService.extract_frames(
                fp,
                sample_rate=config.VIDEO_SAMPLE_RATE,
                max_frames=config.VIDEO_MAX_FRAMES,
                target_height=config.VIDEO_RESIZE_HEIGHT,
            )

            if not success:
                job_result["error"] = metadata.get("error")
                return job_result

            # Parallel OCR over frames
            texts = [None] * len(frame_paths)
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                future_to_idx = {
                    ex.submit(
                        OCRService.extract_text, p, config.OCR_CONFIDENCE_THRESHOLD
                    ): i
                    for i, p in enumerate(frame_paths)
                }
                for fut in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[fut]
                    try:
                        res = fut.result()
                        texts[idx] = res.get("text") if res.get("success") else ""
                    except Exception as e:
                        logger.warning(f"OCR failed for frame {idx}: {str(e)}")
                        texts[idx] = ""

            # Filter non-empty texts and keep mapping to frame indices
            non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
            if not non_empty:
                VideoService.cleanup_frames(metadata.get("frames_dir"))
                job_result["summary"] = {"overall_prediction": "Unable to analyze"}
                return job_result

            indices, texts_only = zip(*non_empty)

            # Batch prediction
            batch_res = PredictionService.predict_batch(list(texts_only))

            frame_predictions = []
            if batch_res.get("success"):
                for idx_in_batch, item in enumerate(batch_res.get("results", [])):
                    frame_idx = indices[idx_in_batch]
                    frame_predictions.append(
                        {
                            "frame_index": int(frame_idx),
                            "extracted_text": item.get("text"),
                            "prediction": item.get("prediction"),
                            "confidence": item.get("confidence"),
                            "probabilities": item.get("probabilities"),
                        }
                    )

            # Summary
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
                fake_count = real_count = 0
                avg_confidence = 0.0
                overall_prediction = "Unable to analyze"

            job_result.update(
                {
                    "frames_analyzed": len(frame_predictions),
                    "frame_predictions": frame_predictions[:5],
                    "summary": {
                        "overall_prediction": overall_prediction,
                        "fake_frames": fake_count,
                        "real_frames": real_count,
                        "average_confidence": round(avg_confidence, 4),
                        "recommendation": f"{fake_count} frames predicted as FAKE out of {len(frame_predictions)} analyzed",
                    },
                    "extracted_content_preview": " ".join(list(texts_only)[:2])[:200]
                    + "...",
                }
            )

            VideoService.cleanup_frames(metadata.get("frames_dir"))
            return job_result

        # If async requested, submit job and return job id
        if run_async:
            job_id = str(uuid.uuid4())
            app.job_store[job_id] = {
                "status": "queued",
                "result": None,
                "started_at": time.time(),
                "finished_at": None,
            }

            def _run_and_store(jid, fp, fname):
                try:
                    app.job_store[jid]["status"] = "running"
                    res = process_video_job(fp, fname)
                    app.job_store[jid]["result"] = res
                    app.job_store[jid]["status"] = "finished"
                    app.job_store[jid]["finished_at"] = time.time()
                except Exception as e:
                    app.job_store[jid]["status"] = "error"
                    app.job_store[jid]["result"] = {"error": str(e)}
                    app.job_store[jid]["finished_at"] = time.time()

            app.executor.submit(_run_and_store, job_id, filepath, filename)

            return jsonify(
                ErrorHandler.format_success_response(
                    {"job_id": job_id}, "Video analysis queued"
                )
            )

        # Otherwise run synchronously (optimized)
        res = process_video_job(filepath, filename)

        if res.get("error"):
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.VIDEO_PROCESSING_FAILED, res.get("error")
                    )
                ),
                500,
            )

        return jsonify(
            ErrorHandler.format_success_response(res, "Video analysis completed")
        )

    except Exception as e:
        logger.error(f"Video upload error: {str(e)}")
        return (
            jsonify(
                ErrorHandler.format_error_response(ErrorCodes.INTERNAL_ERROR, str(e))
            ),
            500,
        )


@app.route("/api/v1/video/youtube", methods=["POST"])
def analyze_youtube():
    """
    Analyze YouTube URL with robust error handling and job management.

    Features:
    - Fast path: captions available -> instant prediction
    - Slow path: full video processing -> async job with polling
    - Thread-safe job store with proper status tracking
    - Comprehensive error handling and logging

    Request JSON: {"url": "https://youtube.com/..", "async": true, "cookies": "..."}
    Response:
    - Fast path: {success: true, data: {prediction, confidence, transcript_source: "captions"}}
    - Slow path: {success: true, data: {job_id: "..."}}
    """
    local_temp_files = []  # Track temp files for cleanup

    try:
        data = request.get_json()
        if not data or "url" not in data:
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INVALID_FILE, "Missing 'url' in request"
                    )
                ),
                400,
            )

        url = data.get("url", "").strip()
        run_async = bool(data.get("async", True))

        logger.info(f"[YouTube] Starting analysis for URL: {url[:50]}...")

        # Validate URL and import service
        try:
            from services import youtube_service

            if not youtube_service.validate_youtube_url(url):
                logger.warning(f"[YouTube] Invalid URL format: {url}")
                return (
                    jsonify(
                        ErrorHandler.format_error_response(
                            ErrorCodes.INVALID_FILE, "Invalid YouTube URL"
                        )
                    ),
                    400,
                )
        except Exception as e:
            logger.error(
                f"[YouTube] Service import/validation failed: {e}", exc_info=True
            )
            if isinstance(e, ModuleNotFoundError):
                missing = getattr(e, "name", None)
                message = (
                    f"Server misconfiguration: missing dependency '{missing}'"
                    if missing
                    else "Server misconfiguration: YouTube service unavailable"
                )
            else:
                message = "Server misconfiguration: YouTube service unavailable"
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.INTERNAL_ERROR,
                        message,
                    )
                ),
                500,
            )

        # Handle optional cookies
        cookiefile_path = None
        cookies_text = data.get("cookies") if isinstance(data, dict) else None
        if cookies_text:
            try:
                tf = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt")
                tf.write(cookies_text)
                tf.flush()
                tf.close()
                cookiefile_path = tf.name
                local_temp_files.append(cookiefile_path)
                logger.info(f"[YouTube] Cookies file created at {cookiefile_path}")
            except Exception as e:
                logger.warning(f"[YouTube] Failed to write temp cookie file: {e}")

        # Probe metadata
        logger.info(f"[YouTube] Probing metadata...")
        try:
            info = youtube_service.probe_metadata(url, cookiefile=cookiefile_path)
        except Exception as e:
            logger.error(f"[YouTube] Failed to probe metadata: {str(e)}")
            # Cleanup and return error
            for temp_file in local_temp_files:
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return (
                jsonify(
                    ErrorHandler.format_error_response(
                        ErrorCodes.VIDEO_PROCESSING_FAILED,
                        f"Failed to analyze video: {str(e)}",
                    )
                ),
                400,
            )

        # Extract video metadata
        metadata = {
            "id": info.get("id"),
            "title": info.get("title"),
            "description": info.get("description"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url"),
        }
        logger.info(
            f"[YouTube] Video: {metadata.get('title')[:60]}... (Duration: {metadata.get('duration')}s)"
        )

        # Try captions first (FAST PATH)
        captions_text = None
        try:
            logger.info(f"[YouTube] Attempting to fetch captions...")
            captions_text = youtube_service.fetch_captions_text(info)
            if captions_text:
                logger.info(f"[YouTube] Captions fetched ({len(captions_text)} chars)")
            else:
                logger.info(
                    f"[YouTube] No captions available, will process video frames"
                )
        except Exception as e:
            logger.warning(f"[YouTube] Captions fetch failed: {e}")

        if captions_text:
            logger.info(f"[YouTube] Using FAST PATH: captions available")
            # Quick prediction using title + description + captions
            combined_text = "\n".join(
                [
                    metadata.get("title", ""),
                    metadata.get("description", ""),
                    captions_text,
                ]
            )

            logger.info(f"[YouTube] Running prediction on combined text...")
            pred = PredictionService.predict(combined_text)

            if not pred.get("success"):
                logger.error(f"[YouTube] Prediction failed: {pred.get('error')}")
                # Cleanup
                for temp_file in local_temp_files:
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                return (
                    jsonify(
                        ErrorHandler.format_error_response(
                            ErrorCodes.PREDICTION_FAILED, pred.get("error")
                        )
                    ),
                    500,
                )

            response_data = {
                "video_id": metadata.get("id"),
                "video_metadata": metadata,
                "transcript_source": "captions",
                "transcript": captions_text,
                "job_id": None,  # No background job for fast path
                "prediction": {
                    "prediction": pred.get("prediction"),
                    "confidence": pred.get("confidence"),
                    "probabilities": pred.get("probabilities"),
                },
            }

            logger.info(f"[YouTube] FAST PATH COMPLETE: {pred.get('prediction')}")
            resp = jsonify(
                ErrorHandler.format_success_response(
                    response_data, "YouTube analysis completed (captions)"
                )
            )

            # Cleanup before returning
            for temp_file in local_temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"[YouTube] Cleaned up temp file: {temp_file}")
                except Exception:
                    pass

            return resp

        # SLOW PATH: Enqueue full processing job
        logger.info(f"[YouTube] Using SLOW PATH: video frame extraction required")
        job_id = str(uuid.uuid4())

        # Initialize job in store
        app.job_store.set(
            job_id,
            {
                "status": "queued",
                "result": None,
                "started_at": time.time(),
                "finished_at": None,
                "error": None,
                "progress_message": "Queued for processing",
            },
        )
        logger.info(f"[YouTube] Job {job_id} created")

        def _process_youtube_background(
            jid, video_url, cookies_file_path, video_metadata
        ):
            """Background job for full video processing with robust error handling"""
            temp_local_files = []

            try:
                # ===== DOWNLOAD =====
                logger.info(f"[Job {jid}] Starting video download...")
                app.job_store.update(
                    jid,
                    {
                        "status": "downloading",
                        "progress_message": "Downloading video...",
                    },
                )

                try:
                    local_path = youtube_service.download_video(
                        video_url, cookiefile=cookies_file_path
                    )
                    temp_local_files.append(local_path)
                    logger.info(f"[Job {jid}] Video downloaded: {local_path}")
                except Exception as e:
                    error_msg = f"Video download failed: {str(e)}"
                    logger.error(f"[Job {jid}] {error_msg}")
                    app.job_store.update(
                        jid,
                        {
                            "status": "error",
                            "error": error_msg,
                            "result": {
                                "error": error_msg,
                                "error_type": "download_failed",
                            },
                            "finished_at": time.time(),
                        },
                    )
                    return

                # ===== EXTRACT FRAMES =====
                logger.info(f"[Job {jid}] Extracting frames...")
                app.job_store.update(
                    jid,
                    {
                        "status": "extracting_frames",
                        "progress_message": "Extracting video frames...",
                    },
                )

                try:
                    success, frame_paths, metadata_fs = VideoService.extract_frames(
                        local_path,
                        sample_rate=config.VIDEO_SAMPLE_RATE,
                        max_frames=config.VIDEO_MAX_FRAMES,
                        target_height=config.VIDEO_RESIZE_HEIGHT,
                    )

                    if not success:
                        error_msg = metadata_fs.get(
                            "error", "Unknown frame extraction error"
                        )
                        logger.error(
                            f"[Job {jid}] Frame extraction failed: {error_msg}"
                        )
                        app.job_store.update(
                            jid,
                            {
                                "status": "error",
                                "error": error_msg,
                                "result": {
                                    "error": error_msg,
                                    "error_type": "frame_extraction_failed",
                                    "video_metadata": video_metadata,
                                },
                                "finished_at": time.time(),
                            },
                        )
                        return

                    frames_dir = metadata_fs.get("frames_dir")
                    if frames_dir:
                        temp_local_files.append(frames_dir)

                    logger.info(f"[Job {jid}] Extracted {len(frame_paths)} frames")
                except Exception as e:
                    error_msg = f"Frame extraction exception: {str(e)}"
                    logger.error(f"[Job {jid}] {error_msg}")
                    app.job_store.update(
                        jid,
                        {
                            "status": "error",
                            "error": error_msg,
                            "result": {
                                "error": error_msg,
                                "error_type": "frame_extraction_exception",
                                "video_metadata": video_metadata,
                            },
                            "finished_at": time.time(),
                        },
                    )
                    return

                # ===== OCR EXTRACTION =====
                logger.info(f"[Job {jid}] Running OCR on {len(frame_paths)} frames...")
                app.job_store.update(
                    jid,
                    {
                        "status": "ocr",
                        "progress_message": f"Extracting text from {len(frame_paths)} frames...",
                    },
                )

                texts = [None] * len(frame_paths)
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                    future_to_idx = {
                        ex.submit(
                            OCRService.extract_text, p, config.OCR_CONFIDENCE_THRESHOLD
                        ): i
                        for i, p in enumerate(frame_paths)
                    }
                    completed_frames = 0
                    for fut in concurrent.futures.as_completed(future_to_idx):
                        idx = future_to_idx[fut]
                        try:
                            res = fut.result()
                            texts[idx] = res.get("text") if res.get("success") else ""
                            completed_frames += 1
                            # Update progress
                            app.job_store.update(
                                jid,
                                {
                                    "progress_message": f"OCR Progress: {completed_frames}/{len(frame_paths)} frames"
                                },
                            )
                        except Exception as e:
                            logger.warning(
                                f"[Job {jid}] OCR failed for frame {idx}: {str(e)}"
                            )
                            texts[idx] = ""

                # Filter out empty texts
                non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
                logger.info(
                    f"[Job {jid}] OCR complete: {len(non_empty)}/{len(frame_paths)} frames with text"
                )

                if not non_empty:
                    logger.warning(f"[Job {jid}] No text detected in any frames")
                    app.job_store.update(
                        jid,
                        {
                            "status": "finished",
                            "progress_message": "Processing complete (no text detected)",
                            "result": {
                                "video_metadata": video_metadata,
                                "frames_analyzed": 0,
                                "frame_predictions": [],
                                "summary": {
                                    "overall_prediction": "Unable to analyze",
                                    "fake_frames": 0,
                                    "real_frames": 0,
                                    "average_confidence": 0.0,
                                    "recommendation": "Insufficient text detected for analysis",
                                },
                                "error_type": None,
                            },
                            "finished_at": time.time(),
                        },
                    )
                    return

                # ===== PREDICTION =====
                logger.info(
                    f"[Job {jid}] Running batch predictions on {len(non_empty)} texts..."
                )
                app.job_store.update(
                    jid,
                    {
                        "status": "predicting",
                        "progress_message": f"Predicting fake/real for {len(non_empty)} texts...",
                    },
                )

                indices, texts_only = zip(*non_empty)
                try:
                    batch_res = PredictionService.predict_batch(list(texts_only))
                except Exception as e:
                    error_msg = f"Batch prediction failed: {str(e)}"
                    logger.error(f"[Job {jid}] {error_msg}")
                    app.job_store.update(
                        jid,
                        {
                            "status": "error",
                            "error": error_msg,
                            "result": {
                                "error": error_msg,
                                "error_type": "prediction_failed",
                                "video_metadata": video_metadata,
                            },
                            "finished_at": time.time(),
                        },
                    )
                    return

                # Process predictions
                frame_predictions = []
                if batch_res.get("success"):
                    for idx_in_batch, item in enumerate(batch_res.get("results", [])):
                        frame_idx = indices[idx_in_batch]
                        frame_predictions.append(
                            {
                                "frame_index": int(frame_idx),
                                "extracted_text": item.get("text"),
                                "prediction": item.get("prediction"),
                                "confidence": item.get("confidence"),
                                "probabilities": item.get("probabilities"),
                            }
                        )

                # Summarize results
                if frame_predictions:
                    fake_count = sum(
                        1 for p in frame_predictions if p["prediction"] == "Fake News"
                    )
                    real_count = sum(
                        1 for p in frame_predictions if p["prediction"] == "Real News"
                    )
                    avg_conf = sum(p["confidence"] for p in frame_predictions) / len(
                        frame_predictions
                    )
                    overall = "Fake News" if fake_count >= real_count else "Real News"
                else:
                    fake_count = real_count = 0
                    avg_conf = 0.0
                    overall = "Unable to analyze"

                logger.info(
                    f"[Job {jid}] Prediction complete: {overall} (fake:{fake_count}, real:{real_count}, conf:{avg_conf:.3f})"
                )

                # Build final result
                result_obj = {
                    "video_metadata": video_metadata,
                    "frames_analyzed": len(frame_predictions),
                    "frame_predictions": frame_predictions[:5],
                    "summary": {
                        "overall_prediction": overall,
                        "fake_frames": fake_count,
                        "real_frames": real_count,
                        "average_confidence": round(avg_conf, 4),
                        "recommendation": (
                            "Use caution: this video may contain false or misleading information."
                            if overall == "Fake News"
                            else (
                                "This video appears genuine based on the extracted text."
                                if overall == "Real News"
                                else "Insufficient text was found for a reliable verdict."
                            )
                        ),
                    },
                    "error_type": None,
                }

                # ===== SUCCESS =====
                logger.info(f"[Job {jid}] PROCESSING COMPLETE - SUCCESS")
                app.job_store.update(
                    jid,
                    {
                        "status": "finished",
                        "progress_message": "Processing complete",
                        "result": result_obj,
                        "finished_at": time.time(),
                    },
                )

            except Exception as e:
                # Generic exception handler
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"[Job {jid}] {error_msg}", exc_info=True)
                app.job_store.update(
                    jid,
                    {
                        "status": "error",
                        "error": error_msg,
                        "result": {
                            "error": error_msg,
                            "error_type": "unexpected_error",
                            "video_metadata": video_metadata,
                        },
                        "finished_at": time.time(),
                    },
                )

            finally:
                # Cleanup all temporary files
                logger.info(f"[Job {jid}] Cleaning up temporary files...")
                for temp_file in temp_local_files:
                    try:
                        if os.path.isdir(temp_file):
                            import shutil

                            shutil.rmtree(temp_file, ignore_errors=True)
                            logger.info(
                                f"[Job {jid}] Removed temp directory: {temp_file}"
                            )
                        elif os.path.isfile(temp_file):
                            os.remove(temp_file)
                            logger.info(f"[Job {jid}] Removed temp file: {temp_file}")
                    except Exception as e:
                        logger.warning(
                            f"[Job {jid}] Failed to cleanup {temp_file}: {e}"
                        )

                # Cleanup cookies file if it exists
                if cookies_file_path:
                    try:
                        os.remove(cookies_file_path)
                        logger.info(
                            f"[Job {jid}] Removed cookies file: {cookies_file_path}"
                        )
                    except Exception:
                        pass

        # Submit background job
        logger.info(f"[YouTube] Submitting background job {job_id}")
        app.executor.submit(
            _process_youtube_background, job_id, url, cookiefile_path, metadata
        )

        response_data = {
            "job_id": job_id,
            "status": "queued",
            "message": "Video processing queued. Poll /api/v1/job/<job_id> for status.",
        }

        logger.info(f"[YouTube] Job {job_id} queued, returning to client")
        return jsonify(
            ErrorHandler.format_success_response(
                response_data, "YouTube video queued for processing"
            )
        )

    except Exception as e:
        logger.error(f"[YouTube] Endpoint exception: {str(e)}", exc_info=True)
        # Cleanup
        for temp_file in local_temp_files:
            try:
                os.remove(temp_file)
            except Exception:
                pass
        return (
            jsonify(
                ErrorHandler.format_error_response(
                    ErrorCodes.INTERNAL_ERROR, f"Server error: {str(e)}"
                )
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


@app.route("/api/v1/job/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """
    Get the status and result of a background processing job.

    Response:
    - status: "queued" | "downloading" | "extracting_frames" | "ocr" | "predicting" | "finished" | "error"
    - result: null during processing, contains result/error when finished
    - error: error message if status is "error"
    - progress_message: human-readable progress update
    """
    job = app.job_store.get(job_id)
    if not job:
        logger.warning(f"[Job {job_id}] Job not found")
        return (
            jsonify(
                ErrorHandler.format_error_response(
                    ErrorCodes.INVALID_FILE, "Job ID not found or expired"
                )
            ),
            404,
        )

    logger.info(f"[Job {job_id}] Status poll - Status: {job.get('status')}")

    return jsonify(
        ErrorHandler.format_success_response(
            {
                "job_id": job_id,
                "status": job.get("status"),
                "result": job.get("result"),
                "error": job.get("error"),
                "progress_message": job.get("progress_message", ""),
                "started_at": job.get("started_at"),
                "finished_at": job.get("finished_at"),
            },
            "Job status retrieved",
        )
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
