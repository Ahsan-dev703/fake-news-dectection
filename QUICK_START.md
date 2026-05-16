# ⚡ Quick Start Guide

Get the Multimodal Fake News Detection System running in 5 minutes.

## Step 1: Install Dependencies

### Backend

```bash
# Navigate to project root
cd fake-news-detection

# Install Python packages
pip install -r requirements.txt

# Or with virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Step 2: Start Backend

```bash
# From project root
python backend/app.py

# Or from backend directory
cd backend
python app.py
```

**Expected output:**

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### First Time Setup Notes

- ✅ Backend will auto-initialize services on first request
- ⏳ EasyOCR will download language models (~100MB) on first use
- 🎯 Model loads from `models/model.pkl`

**If you see errors:**

```bash
# Make sure model file exists
ls models/model.pkl

# If missing, run the training notebook
jupyter notebook notebooks/experimentation.ipynb
```

## Step 3: Start Frontend

```bash
cd frontend
npm run dev

# Frontend runs on http://localhost:5173
```

## Step 4: Open and Test

Visit: **http://localhost:5173**

### Test Each Feature

**1. Text Analysis**

- Tab: "📝 Text"
- Paste any news text
- Click "Analyze Text"
- See prediction + confidence

**2. Image Analysis**

- Tab: "📸 Image"
- Upload any image (JPG, PNG, etc.)
- System extracts text and predicts
- See extracted text + prediction

**3. Video Analysis**

- Tab: "🎬 Video"
- Upload any video (MP4, AVI, etc.)
- System extracts frames, analyzes each
- See summary of fake/real frames

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error: ModuleNotFoundError**

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

**Error: Port 5000 in use**

```bash
# Use different port (edit config.py)
export FLASK_PORT=5001
python backend/app.py

# Then update frontend API URL in App.jsx:
# const API_BASE_URL = "http://127.0.0.1:5001"
```

**Error: models/model.pkl not found**

```bash
# Train the model first
jupyter notebook notebooks/experimentation.ipynb
# Run all cells to generate models/model.pkl
```

### Frontend Won't Load

**Error: Cannot connect to API**

1. Verify backend is running on port 5000
2. Check CORS is enabled in `backend/config.py`
3. Check frontend API URL matches backend URL

**Error: Blank page**

```bash
# Clear browser cache
npm run dev  # Restart dev server
```

### OCR Not Working

**Error: EasyOCR not found**

```bash
pip install easyocr
# First run takes 5-10 seconds (downloads models)
```

**Error: Out of memory with video**

- Reduce `VIDEO_MAX_FRAMES` in `.env`
- Or increase `VIDEO_SAMPLE_RATE` (extract fewer frames)

---

## 📝 Configuration

### Environment Variables (`.env`)

Located in project root:

```env
# Flask
FLASK_ENV=development
DEBUG=True

# File sizes
MAX_IMAGE_SIZE=52428800      # 50MB
MAX_VIDEO_SIZE=536870912     # 500MB

# OCR
OCR_CONFIDENCE=0.3

# Video
VIDEO_SAMPLE_RATE=5          # Every 5th frame
VIDEO_MAX_FRAMES=30          # Max 30 frames
```

To change: Edit `.env` and restart backend

---

## 🧪 Quick API Test

### Using cURL

```bash
# Test text prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Breaking news about climate"}'

# Expected response
# {"success": true, "data": {"prediction": "Real News", ...}}
```

### Using Python

```python
import requests

# Text prediction
response = requests.post(
    "http://localhost:5000/api/v1/text/predict",
    json={"text": "some news text"}
)
print(response.json())
```

### Using JavaScript

```javascript
// Text prediction
fetch("http://localhost:5000/api/v1/text/predict", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ text: "some news text" }),
})
  .then((r) => r.json())
  .then((data) => console.log(data));
```

---

## 📊 What Gets Analyzed

### Text Mode

✅ Direct text analysis
✅ Confidence score
✅ Fake/Real probabilities

### Image Mode

✅ OCR text extraction
✅ Extracted text analysis
✅ Image manipulation detection
✅ Per-image prediction

### Video Mode

✅ Automatic frame extraction
✅ Text extraction from each frame
✅ Per-frame predictions
✅ Summary statistics (fake/real frames)
✅ Average confidence

---

## 📁 Important Files

| File                   | Purpose                  |
| ---------------------- | ------------------------ |
| `backend/app.py`       | Main API server          |
| `backend/config.py`    | Configuration management |
| `backend/services/`    | ML/processing services   |
| `frontend/src/App.jsx` | React UI component       |
| `frontend/src/App.css` | Styling                  |
| `models/model.pkl`     | Trained ML model         |
| `.env`                 | Environment variables    |
| `requirements.txt`     | Python dependencies      |

---

## 🚀 Next Steps

1. **Read Full Docs**: See [README.md](README.md)
2. **API Examples**: See [API_USAGE.md](API_USAGE.md)
3. **Backend Docs**: See [backend/README.md](backend/README.md)
4. **Deploy**: See deployment section in [README.md](README.md)

---

## 💡 Tips

- **For faster testing**: Use smaller video files (reduce frames)
- **For better accuracy**: Ensure good image/video quality with clear text
- **For production**: Set `DEBUG=False` and `FLASK_ENV=production`
- **For API testing**: Use provided examples in [API_USAGE.md](API_USAGE.md)

---

## ✅ You're Ready!

- Backend: http://localhost:5000
- Frontend: http://localhost:5173
- Try all three modes (text, image, video)
- Check console for any errors

Need help? Check [backend/README.md](backend/README.md) for detailed troubleshooting.
