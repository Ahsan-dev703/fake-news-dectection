# Backend API Documentation

This is the Flask REST API backend for the Multimodal Fake News Detection System.

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt

# Create .env file (copy from template)
cp ../.env.example .env  # Or create manually
```

### Running the Server

```bash
# Development
python app.py

# Production (with Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Server will be available at `http://localhost:5000`

---

## 📂 File Structure

```
backend/
├── app.py                    # Main Flask application (500+ lines)
│                             # - All route handlers
│                             # - CORS setup
│                             # - Error handling
│
├── config.py                 # Configuration management
│                             # - Environment variables
│                             # - Settings for dev/prod
│
├── services/                 # Service layer (business logic)
│   ├── __init__.py
│   ├── prediction_service.py # ML model inference
│   ├── ocr_service.py        # OCR text extraction
│   ├── image_service.py      # Image processing & analysis
│   └── video_service.py      # Video processing & frame extraction
│
├── utils/                    # Utility functions
│   ├── __init__.py
│   └── validators.py         # File validation, error handling
│
├── uploads/                  # Temporary uploaded files storage
├── models/                   # ML model artifacts
│   └── model.pkl            # Serialized sklearn model
│
└── requirements.txt          # Python dependencies
```

---

## 🔧 Services Overview

### PredictionService

Wraps the ML model and vectorizer for inference.

**Key Methods**:

- `initialize(model_path)` - Load model on startup
- `predict(text)` - Single prediction
- `predict_batch(texts)` - Multiple predictions
- `get_model_info()` - Model metadata

**Usage**:

```python
from services import PredictionService

# Initialize once on startup
PredictionService.initialize("models/model.pkl")

# Predict
result = PredictionService.predict("news text here")
# Returns: {
#   "success": bool,
#   "prediction": "Real News|Fake News",
#   "confidence": 0.95,
#   "probabilities": {"fake": 0.05, "real": 0.95}
# }
```

### OCRService

Extracts text from images using EasyOCR.

**Key Methods**:

- `initialize(languages)` - Load OCR model
- `extract_text(image_path, confidence_threshold)` - Extract from file
- `extract_text_from_bytes(image_bytes, threshold)` - Extract from bytes

**Features**:

- Confidence filtering
- Multi-language support (default: English)
- Structured output with bounding boxes
- Error handling with fallback

### ImageService

Processes images for analysis and detection.

**Key Methods**:

- `get_image_info(image_path)` - Get metadata (dimensions, format)
- `resize_image(image_path, max_height)` - Optimize for OCR
- `optimize_for_ocr(image_path)` - Enhance contrast, denoise
- `detect_image_manipulation(image_path)` - Deepfake detection

**Features**:

- Bilat filtering for denoising
- CLAHE contrast enhancement
- Frequency-based manipulation detection
- Lossless image optimization

### VideoService

Processes videos for analysis.

**Key Methods**:

- `get_video_info(video_path)` - Get video metadata
- `extract_frames(video_path, sample_rate, max_frames)` - Extract key frames
- `cleanup_frames(frames_dir)` - Delete temp files
- `detect_scene_changes(frame_paths, threshold)` - Scene detection

**Features**:

- Smart frame sampling (every Nth frame)
- Automatic resizing for memory efficiency
- Histogram-based scene change detection
- Temporary frame management

---

## 📝 API Endpoints

### Health & Info

| Method | Endpoint       | Purpose                |
| ------ | -------------- | ---------------------- |
| GET    | `/`            | Health check           |
| GET    | `/health`      | Detailed health status |
| GET    | `/api/v1/info` | API info & config      |

### Text Analysis

| Method | Endpoint               | Purpose                      |
| ------ | ---------------------- | ---------------------------- |
| POST   | `/predict`             | Legacy text prediction       |
| POST   | `/api/v1/text/predict` | Enhanced text (single/batch) |

### Image Analysis

| Method | Endpoint               | Purpose                  |
| ------ | ---------------------- | ------------------------ |
| POST   | `/api/v1/image/upload` | Full image analysis      |
| POST   | `/api/v1/image/ocr`    | OCR only (no prediction) |

### Video Analysis

| Method | Endpoint               | Purpose             |
| ------ | ---------------------- | ------------------- |
| POST   | `/api/v1/video/upload` | Full video analysis |
| POST   | `/api/v1/video/frames` | Extract frames only |

---

## 🔐 Configuration

### Environment Variables

See `../.env` file:

```env
# Flask
FLASK_ENV=development
DEBUG=True

# Upload Limits
MAX_IMAGE_SIZE=52428800        # 50MB
MAX_VIDEO_SIZE=536870912       # 500MB

# OCR Settings
OCR_ENGINE=easyocr
OCR_CONFIDENCE=0.3

# Video Processing
VIDEO_SAMPLE_RATE=5            # Extract every 5th frame
VIDEO_MAX_FRAMES=30            # Max 30 frames

# Model Path
MODEL_PATH=models/model.pkl
```

### Changing Configuration

Edit `.env` and restart server. For production:

```bash
export FLASK_ENV=production
export DEBUG=False
python app.py
```

---

## 📊 Logging

All operations are logged to console with structure:

```
2024-05-16 10:30:45 - app - INFO - Loading model from: models/model.pkl
2024-05-16 10:30:46 - app - INFO - Model loaded successfully
2024-05-16 10:30:47 - app - INFO - Image uploaded: backend/uploads/20240516_103047_test.jpg
```

Check logs for:

- Service initialization status
- File operations
- OCR/prediction results
- Errors and exceptions

---

## ⚡ Performance Tips

1. **Model Loading**: Loaded once on first request, cached in memory
2. **OCR Initialization**: Takes ~5-10s first time (downloads models), then instant
3. **Video Processing**: Extract fewer frames (`VIDEO_MAX_FRAMES=10` for speed)
4. **Large Files**: Implement async processing with Celery for production

---

## 🐛 Common Issues

### ImportError: No module named 'easyocr'

```bash
pip install easyocr
# First run downloads ~100MB language models
```

### Model not found: models/model.pkl

Ensure you have trained the model. Check:

```bash
ls -la models/
```

If missing, run the training notebook in `/notebooks/experimentation.ipynb`

### CUDA/GPU not available

EasyOCR will automatically fall back to CPU (slower but works). To enable GPU:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Port 5000 already in use

```bash
# Find process using port 5000
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Kill process or use different port
export FLASK_PORT=5001
```

---

## 🔄 Request/Response Examples

### Text Prediction

**Request**:

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Breaking news: ....."}'
```

**Response**:

```json
{
  "success": true,
  "message": "Text analysis completed",
  "data": {
    "text_preview": "Breaking news: ...",
    "prediction": "Real News",
    "confidence": 0.8723,
    "probabilities": {
      "fake": 0.1277,
      "real": 0.8723
    }
  }
}
```

### Image Analysis

**Request**:

```bash
curl -X POST http://localhost:5000/api/v1/image/upload \
  -F "file=@news_image.jpg"
```

**Response**:

```json
{
  "success": true,
  "message": "Image analysis completed",
  "data": {
    "file_name": "20240516_103047_news_image.jpg",
    "ocr": {
      "success": true,
      "extracted_text": "Breaking news headline...",
      "confidence": 0.92,
      "text_count": 5
    },
    "prediction": {
      "success": true,
      "prediction": "Real News",
      "confidence": 0.85
    },
    "manipulation_analysis": {
      "success": true,
      "manipulation_score": 0.23
    }
  }
}
```

---

## 🚀 Deployment Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Set `FLASK_ENV=production`
- [ ] Verify `MODEL_PATH` is accessible
- [ ] Update `CORS_ORIGINS` for your domain
- [ ] Use Gunicorn (4+ workers) instead of Flask dev server
- [ ] Set up reverse proxy (Nginx)
- [ ] Enable HTTPS/SSL
- [ ] Set up error monitoring (Sentry)
- [ ] Configure file upload directory with sufficient space
- [ ] Set up log rotation

---

## 📚 Further Reading

- [Flask Documentation](https://flask.palletsprojects.com/)
- [EasyOCR Docs](https://github.com/JaidedAI/EasyOCR)
- [OpenCV Docs](https://docs.opencv.org/)
- [scikit-learn Models](https://scikit-learn.org/)

---

**Last Updated**: May 16, 2026
