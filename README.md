# Multimodal Fake News Detection System v2.0

> Advanced ML system for detecting fake news from text, images, and videos using state-of-the-art AI/ML techniques.

## 🎯 Key Features

- **Text Analysis**: Direct text prediction with 98.69% accuracy
- **Image Analysis**: OCR-based text extraction + fake news detection
- **Video Analysis**: Frame extraction + OCR + predictions with summary metrics
- **Production-Ready**: Error handling, validation, logging, async-safe operations
- **Modular Architecture**: Clean separation of concerns - services, utilities, routes
- **Scalable Design**: Built for deployment, configuration management via environment variables

## 📊 System Overview

```
Frontend (React Vite)
    ↓
API Gateway (Flask)
    ↓
Service Layer
    ├── PredictionService (TF-IDF + Logistic Regression)
    ├── OCRService (EasyOCR)
    ├── ImageService (OpenCV)
    └── VideoService (OpenCV)
    ↓
ML Model (sklearn)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- Git

### Backend Setup

1. **Install dependencies**:

```bash
cd backend
pip install -r ../requirements.txt
```

2. **Create environment file** (`.env`):

```bash
# Copy existing .env or create new one with settings
FLASK_ENV=development
DEBUG=True
MODEL_PATH=models/model.pkl
```

3. **Run backend**:

```bash
python app.py
```

Backend runs on `http://localhost:5000`

### Frontend Setup

1. **Install dependencies**:

```bash
cd frontend
npm install
```

2. **Run development server**:

```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

3. **Build for production**:

```bash
npm run build
```

---

## 📚 API Documentation

### Health & Info Endpoints

**GET** `/`

- Health check
- Returns: Status, version, supported modes

**GET** `/health`

- Detailed health status
- Returns: Service status, model info

**GET** `/api/v1/info`

- API and model configuration
- Returns: Version, supported modes, config details

---

### Text Analysis

**POST** `/predict` (legacy)

```json
{
  "text": "news article text here..."
}
```

Response:

```json
{
  "success": true,
  "data": {
    "prediction": "Real News",
    "confidence": 0.95,
    "probabilities": { "fake": 0.05, "real": 0.95 }
  }
}
```

**POST** `/api/v1/text/predict` (recommended)

- Single: `{"text": "..."}`
- Batch: `{"texts": ["...", "..."]}`

---

### Image Analysis

**POST** `/api/v1/image/upload`

- Request: `multipart/form-data` with `file` field
- Returns: Prediction + OCR results + manipulation analysis

**POST** `/api/v1/image/ocr`

- Extract text from image only
- Request: `multipart/form-data` with `file` field
- Returns: Extracted text, confidence, raw OCR results

---

### Video Analysis

**POST** `/api/v1/video/upload`

- Request: `multipart/form-data` with `file` field
- Extracts frames, performs OCR, predicts per-frame
- Returns: Summary prediction, frame-by-frame results

**POST** `/api/v1/video/frames`

- Extract frames only (no analysis)
- Returns: Frame count, metadata

---

## 🏗️ Project Structure

```
fake-news-detection/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration management
│   ├── services/
│   │   ├── __init__.py
│   │   ├── prediction_service.py   # Model inference
│   │   ├── ocr_service.py          # Text extraction
│   │   ├── image_service.py        # Image processing
│   │   └── video_service.py        # Video processing
│   ├── utils/
│   │   ├── __init__.py
│   │   └── validators.py      # File validation, error handling
│   ├── uploads/               # Temporary file storage
│   ├── models/
│   │   └── model.pkl         # Trained ML model
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React component
│   │   ├── App.css            # Styling
│   │   ├── main.jsx
│   │   └── assets/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── eslint.config.js
│
├── src/                       # Original ML code (for reference)
│   ├── data_preprocessing.py
│   ├── feature_engineering.py
│   ├── model.py
│   └── predict.py
│
├── data/
│   ├── Fake.csv
│   └── True.csv
│
├── notebooks/
│   └── experimentation.ipynb  # Training notebook
│
├── models/
│   └── model.pkl             # Serialized model
│
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## ⚙️ Configuration

### Environment Variables (`.env`)

| Variable            | Default          | Description              |
| ------------------- | ---------------- | ------------------------ |
| `FLASK_ENV`         | development      | Environment type         |
| `DEBUG`             | True             | Debug mode               |
| `CORS_ORIGINS`      | \*               | Allowed CORS origins     |
| `UPLOAD_FOLDER`     | backend/uploads  | File upload directory    |
| `MAX_IMAGE_SIZE`    | 52428800         | Max image size (50MB)    |
| `MAX_VIDEO_SIZE`    | 536870912        | Max video size (500MB)   |
| `OCR_ENGINE`        | easyocr          | OCR library to use       |
| `OCR_CONFIDENCE`    | 0.3              | OCR confidence threshold |
| `VIDEO_SAMPLE_RATE` | 5                | Extract every Nth frame  |
| `VIDEO_MAX_FRAMES`  | 30               | Max frames to process    |
| `MODEL_PATH`        | models/model.pkl | Path to ML model         |

---

## 🔐 Production Deployment

### Security Best Practices

1. **Set `DEBUG=False`** in `.env`
2. **Limit CORS origins**: `CORS_ORIGINS=https://yourdomain.com`
3. **Use environment variables** for sensitive data
4. **Implement rate limiting** on API endpoints
5. **Add authentication** (JWT tokens) if needed
6. **Use HTTPS/SSL** in production

### Recommended Deployment Stack

- **Backend**: Gunicorn + Nginx
- **Frontend**: Served by CDN or static hosting
- **Database**: Optional (for logging predictions)
- **Monitoring**: Prometheus + Grafana

#### Docker Deployment

```dockerfile
# backend/Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 📈 Model Information

- **Algorithm**: Logistic Regression
- **Features**: TF-IDF (max 5000 features)
- **Training Data**: Fake.csv + True.csv
- **Accuracy**: 98.69%
- **Training Framework**: scikit-learn

### Model Retraining

To retrain with new data:

```bash
python scripts/train.py --data data/ --output models/model.pkl
```

(Requires creating `scripts/train.py` - not yet implemented)

---

## 🧪 Testing

### Manual Testing

1. **Text Analysis**:

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"This is a test news article"}'
```

2. **Image Upload**:

```bash
curl -X POST http://localhost:5000/api/v1/image/upload \
  -F "file=@test_image.jpg"
```

3. **Video Upload**:

```bash
curl -X POST http://localhost:5000/api/v1/video/upload \
  -F "file=@test_video.mp4"
```

### Automated Testing

(To be implemented: Unit tests for services, integration tests)

---

## 🐛 Troubleshooting

### Backend Won't Start

- Check `.env` file exists and is valid
- Ensure `models/model.pkl` exists
- Run `pip install -r requirements.txt` again

### OCR Not Working

- Verify EasyOCR installed: `python -c "import easyocr; easyocr.Reader(['en'])"`
- First run downloads language models (~100MB)
- Check logs for detailed error messages

### CORS Errors

- Verify frontend URL is in `CORS_ORIGINS`
- Check browser console for exact error message
- In development, can set `CORS_ORIGINS=*`

### Out of Memory (Video Processing)

- Reduce `VIDEO_MAX_FRAMES` in `.env`
- Increase `VIDEO_SAMPLE_RATE` to skip more frames
- Deploy on machine with more RAM

---

## 📝 API Response Formats

### Success Response

```json
{
  "success": true,
  "message": "Operation completed",
  "data": {
    /* operation-specific data */
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    /* optional details */
  }
}
```

---

## 🔄 Future Enhancements

- [ ] Async video processing (Celery + Redis)
- [ ] Database for prediction history
- [ ] User authentication system
- [ ] Advanced deepfake detection CNN
- [ ] Audio analysis with Whisper
- [ ] Multi-language OCR support
- [ ] Model versioning and A/B testing
- [ ] Real-time streaming analysis
- [ ] Mobile app (React Native)

---

## 📄 License

MIT License - Feel free to use and modify

---

## 👥 Support

For issues or questions:

1. Check the troubleshooting section
2. Review API documentation
3. Check backend logs: `backend/app.py` output
4. Check browser console for frontend errors

---

**Version**: 2.0  
**Last Updated**: May 16, 2026  
**Status**: Production Ready
