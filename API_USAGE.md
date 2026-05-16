# API Usage Examples

Complete guide with code examples for using the Multimodal Fake News Detection API.

## 📋 Table of Contents

1. [Text Analysis](#text-analysis)
2. [Image Analysis](#image-analysis)
3. [Video Analysis](#video-analysis)
4. [Error Handling](#error-handling)
5. [Python Examples](#python-examples)
6. [JavaScript Examples](#javascript-examples)

---

## Text Analysis

### Single Text Prediction

**cURL**:

```bash
curl -X POST http://localhost:5000/api/v1/text/predict \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A major breakthrough in renewable energy was announced today as scientists develop more efficient solar panels"
  }'
```

**Response**:

```json
{
  "success": true,
  "message": "Text analysis completed",
  "data": [
    {
      "prediction": "Real News",
      "confidence": 0.9245,
      "probabilities": {
        "fake": 0.0755,
        "real": 0.9245
      }
    }
  ]
}
```

### Batch Text Prediction

Process multiple texts in one request:

**cURL**:

```bash
curl -X POST http://localhost:5000/api/v1/text/predict \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "First news article here...",
      "Second news article here...",
      "Third news article here..."
    ]
  }'
```

**Response**:

```json
{
  "success": true,
  "message": "Batch prediction completed for 3 texts",
  "data": [
    {
      "text": "First news article here...",
      "prediction": "Real News",
      "confidence": 0.87
    },
    {
      "text": "Second news article here...",
      "prediction": "Fake News",
      "confidence": 0.92
    },
    {
      "text": "Third news article here...",
      "prediction": "Real News",
      "confidence": 0.79
    }
  ]
}
```

---

## Image Analysis

### Upload Image with Full Analysis

Extract text from image and predict fake news:

**cURL**:

```bash
curl -X POST http://localhost:5000/api/v1/image/upload \
  -F "file=@path/to/image.jpg"
```

**Response**:

```json
{
  "success": true,
  "message": "Image analysis completed",
  "data": {
    "file_name": "20240516_103047_image.jpg",
    "image_info": {
      "success": true,
      "width": 1920,
      "height": 1080,
      "format": "JPEG"
    },
    "ocr": {
      "success": true,
      "extracted_text": "Breaking news: Scientists discover new element\nConfirmed by major laboratories worldwide",
      "confidence": 0.91,
      "text_count": 2
    },
    "prediction": {
      "success": true,
      "prediction": "Real News",
      "confidence": 0.88,
      "probabilities": {
        "fake": 0.12,
        "real": 0.88
      }
    },
    "manipulation_analysis": {
      "success": true,
      "manipulation_score": 0.15,
      "interpretation": "Appears genuine"
    }
  }
}
```

### Extract Text Only (OCR)

Get extracted text without fake news prediction:

**cURL**:

```bash
curl -X POST http://localhost:5000/api/v1/image/ocr \
  -F "file=@path/to/image.jpg"
```

**Response**:

```json
{
  "success": true,
  "message": "OCR extraction completed",
  "data": {
    "file_name": "20240516_103047_image.jpg",
    "extracted_text": "Breaking news: Scientists discover new element",
    "confidence": 0.91,
    "text_count": 2,
    "raw_results": [
      {
        "text": "Breaking news:",
        "confidence": 0.95,
        "bbox": [
          [100, 50],
          [400, 50],
          [400, 100],
          [100, 100]
        ]
      },
      {
        "text": "Scientists discover new element",
        "confidence": 0.87,
        "bbox": [
          [100, 110],
          [600, 110],
          [600, 160],
          [100, 160]
        ]
      }
    ]
  }
}
```

---

## Video Analysis

### Analyze Video (Full Processing)

Extract frames, perform OCR, and predict:

**cURL**:

```bash
curl -X POST http://localhost:5000/api/v1/video/upload \
  -F "file=@path/to/video.mp4"
```

**Response** (truncated):

```json
{
  "success": true,
  "message": "Video analysis completed",
  "data": {
    "file_name": "20240516_103047_video.mp4",
    "video_info": {
      "success": true,
      "frame_count": 300,
      "fps": 30,
      "duration_seconds": 10,
      "duration_readable": "0m 10s"
    },
    "frames_analyzed": 8,
    "frame_predictions": [
      {
        "frame_index": 0,
        "extracted_text": "Breaking news: Major incident reported...",
        "ocr_confidence": 0.89,
        "prediction": "Real News",
        "confidence": 0.92,
        "probabilities": {
          "fake": 0.08,
          "real": 0.92
        }
      },
      {
        "frame_index": 5,
        "extracted_text": "Live coverage from the scene",
        "ocr_confidence": 0.85,
        "prediction": "Real News",
        "confidence": 0.87
      }
    ],
    "summary": {
      "overall_prediction": "Real News",
      "fake_frames": 1,
      "real_frames": 7,
      "average_confidence": 0.8912,
      "recommendation": "1 frames predicted as FAKE out of 8 analyzed"
    },
    "extracted_content_preview": "Breaking news: Major incident reported... Live coverage from the scene..."
  }
}
```

### Extract Frames Only

Get frames without analysis:

**cURL**:

```bash
curl -X POST http://localhost:5000/api/v1/video/frames \
  -F "file=@path/to/video.mp4"
```

**Response**:

```json
{
  "success": true,
  "message": "Frame extraction completed",
  "data": {
    "file_name": "20240516_103047_video.mp4",
    "total_frames_extracted": 10,
    "video_metadata": {
      "total_frames": 300,
      "extracted_frames": 10,
      "fps": 30,
      "sample_rate": 5,
      "frames_dir": "backend/uploads/temp_frames"
    }
  }
}
```

---

## Error Handling

### Common Error Responses

**Invalid File Type**:

```json
{
  "success": false,
  "error": "Image extension must be one of {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}",
  "error_code": "INVALID_FILE"
}
```

**File Too Large**:

```json
{
  "success": false,
  "error": "Image size exceeds 50MB limit",
  "error_code": "INVALID_FILE"
}
```

**Model Not Found**:

```json
{
  "success": false,
  "error": "Model failed to load. Please check model file.",
  "error_code": "MODEL_NOT_FOUND"
}
```

**OCR Failed**:

```json
{
  "success": false,
  "error": "OCR extraction failed: ...",
  "error_code": "OCR_FAILED"
}
```

**No File Provided**:

```json
{
  "success": false,
  "error": "No file provided. Use 'file' field in multipart form",
  "error_code": "INVALID_FILE"
}
```

---

## Python Examples

### Using Requests Library

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# ============================================================
# TEXT ANALYSIS
# ============================================================

def predict_text(text):
    """Predict single text"""
    response = requests.post(
        f"{BASE_URL}/api/v1/text/predict",
        json={"text": text}
    )
    return response.json()

def predict_texts(texts):
    """Batch predict multiple texts"""
    response = requests.post(
        f"{BASE_URL}/api/v1/text/predict",
        json={"texts": texts}
    )
    return response.json()

# Usage
result = predict_text("Breaking news about renewable energy")
print(f"Prediction: {result['data'][0]['prediction']}")
print(f"Confidence: {result['data'][0]['confidence']:.2%}")

# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(image_path):
    """Analyze image with OCR and fake news detection"""
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/api/v1/image/upload",
            files=files
        )
    return response.json()

def extract_image_text(image_path):
    """Extract text from image only"""
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/api/v1/image/ocr",
            files=files
        )
    return response.json()

# Usage
result = analyze_image("path/to/image.jpg")
if result['success']:
    print(f"Extracted Text: {result['data']['ocr']['extracted_text']}")
    print(f"Prediction: {result['data']['prediction']['prediction']}")

# ============================================================
# VIDEO ANALYSIS
# ============================================================

def analyze_video(video_path):
    """Analyze video with frame extraction and text analysis"""
    with open(video_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/api/v1/video/upload",
            files=files
        )
    return response.json()

def extract_video_frames(video_path):
    """Extract frames without analysis"""
    with open(video_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/api/v1/video/frames",
            files=files
        )
    return response.json()

# Usage
result = analyze_video("path/to/video.mp4")
if result['success']:
    summary = result['data']['summary']
    print(f"Overall Prediction: {summary['overall_prediction']}")
    print(f"Fake Frames: {summary['fake_frames']}")
    print(f"Real Frames: {summary['real_frames']}")

# ============================================================
# ERROR HANDLING
# ============================================================

def safe_predict(text):
    """Predict with error handling"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/text/predict",
            json={"text": text},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data'][0]
            else:
                print(f"API Error: {data.get('error')}")
                return None
        else:
            print(f"HTTP Error: {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("Cannot connect to backend")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
result = safe_predict("Some news text")
if result:
    print(f"✓ {result['prediction']} ({result['confidence']:.1%} confidence)")
```

---

## JavaScript Examples

### Using Fetch API (Frontend)

```javascript
const API_BASE_URL = "http://localhost:5000";

// ============================================================
// TEXT ANALYSIS
// ============================================================

async function predictText(text) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/text/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    return { success: false, error: error.message };
  }
}

async function predictTexts(texts) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/text/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts }),
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    return { success: false, error: error.message };
  }
}

// Usage
predictText("Breaking news about climate change").then((result) => {
  if (result.success) {
    console.log(`Prediction: ${result.data[0].prediction}`);
    console.log(`Confidence: ${(result.data[0].confidence * 100).toFixed(1)}%`);
  } else {
    console.error(result.error);
  }
});

// ============================================================
// IMAGE ANALYSIS
// ============================================================

async function analyzeImage(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/v1/image/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    return { success: false, error: error.message };
  }
}

async function extractImageText(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/v1/image/ocr`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    return { success: false, error: error.message };
  }
}

// Usage
document.getElementById("imageInput").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const result = await analyzeImage(file);
  if (result.success) {
    document.getElementById("prediction").textContent =
      result.data.prediction.prediction;
    document.getElementById("extractedText").textContent =
      result.data.ocr.extracted_text;
  } else {
    alert("Error: " + result.error);
  }
});

// ============================================================
// VIDEO ANALYSIS
// ============================================================

async function analyzeVideo(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/v1/video/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error:", error);
    return { success: false, error: error.message };
  }
}

// Usage with progress
async function analyzeVideoWithProgress(file, onProgress) {
  onProgress(0);

  const result = await analyzeVideo(file);

  onProgress(100);

  if (result.success) {
    const summary = result.data.summary;
    return {
      prediction: summary.overall_prediction,
      fakeFrames: summary.fake_frames,
      realFrames: summary.real_frames,
      confidence: summary.average_confidence,
    };
  } else {
    throw new Error(result.error);
  }
}

// Usage
document.getElementById("videoInput").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const result = await analyzeVideoWithProgress(file, (progress) => {
      document.getElementById("progress").style.width = progress + "%";
    });

    document.getElementById("videoPrediction").textContent = result.prediction;
    document.getElementById("videoStats").innerHTML =
      `Fake: ${result.fakeFrames} | Real: ${result.realFrames} | 
       Confidence: ${(result.confidence * 100).toFixed(1)}%`;
  } catch (error) {
    alert("Error: " + error.message);
  }
});

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function formatConfidence(confidence) {
  return `${(confidence * 100).toFixed(1)}%`;
}

function getPredictionColor(prediction) {
  return prediction === "Real News" ? "green" : "red";
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    return data.status === "healthy";
  } catch {
    return false;
  }
}

// Usage
checkHealth().then((isHealthy) => {
  if (!isHealthy) {
    alert("Backend is not responding. Please start the server.");
  }
});
```

### Using Axios

```javascript
import axios from "axios";

const API_BASE_URL = "http://localhost:5000";
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Text prediction
export const predictText = (text) => api.post("/api/v1/text/predict", { text });

// Batch prediction
export const predictTexts = (texts) =>
  api.post("/api/v1/text/predict", { texts });

// Image analysis
export const analyzeImage = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/v1/image/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// Video analysis
export const analyzeVideo = (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/v1/video/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
};

// Health check
export const checkHealth = () => api.get("/health");
```

---

## Testing the API

### Health Check

```bash
curl http://localhost:5000/health
```

### Info Endpoint

```bash
curl http://localhost:5000/api/v1/info
```

### Quick Text Test

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Test news article"}'
```

---

**For more information, see the main [README.md](../README.md) file.**
