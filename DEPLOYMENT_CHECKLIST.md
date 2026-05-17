# 🚀 Deployment & Verification Checklist

## Pre-Deployment Checks

### Backend Environment

- [ ] Python 3.8+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] yt-dlp latest version: `pip install --upgrade yt-dlp`
- [ ] FFmpeg installed (for audio extraction)
- [ ] OpenCV working: `python -c "import cv2; print(cv2.__version__)"`
- [ ] Flask-CORS installed

### Frontend Environment

- [ ] Node.js 16+ installed
- [ ] npm packages installed: `npm install`
- [ ] React 18+ available
- [ ] Vite/build tool configured

### Network & Access

- [ ] Backend will run on `http://127.0.0.1:5000`
- [ ] Frontend will run on local dev server (default `http://localhost:5173`)
- [ ] CORS enabled between frontend and backend
- [ ] No firewall blocking localhost communication

---

## Deployment Steps

### 1. Update Code

```bash
# Ensure latest code is in place
# Check files modified:
# - backend/app.py
# - frontend/src/App.jsx
```

### 2. Start Backend

```bash
cd backend
python app.py
# Should show: * Running on http://127.0.0.1:5000/
```

### 3. Start Frontend

```bash
cd frontend
npm run dev
# Should show: Local:   http://localhost:5173
```

### 4. Verify Health

```bash
# Backend health
curl http://127.0.0.1:5000/health

# Should return: {"status": "healthy", ...}
```

---

## Functional Testing

### Test 1: System Startup

- [ ] Backend starts without errors
- [ ] Frontend loads without JavaScript errors
- [ ] CORS requests work (check Network tab in DevTools)
- [ ] Models loaded: Check backend logs for "All services initialized"

### Test 2: Text Analysis (Baseline)

- [ ] Go to Text tab
- [ ] Enter sample text
- [ ] Click "Predict"
- [ ] Result appears within 2-5 seconds
- [ ] Shows prediction and confidence

### Test 3: Fast Path (YouTube with Captions)

- [ ] Go to YouTube tab
- [ ] Enter URL: `https://www.youtube.com/watch?v=jNQXAC9IVRw`
- [ ] Click "Analyze YouTube URL"
- [ ] Within 5-10 seconds:
  - [ ] Status message appears
  - [ ] Result displays
  - [ ] Shows "transcript_source": "captions"

### Test 4: Slow Path (YouTube without Captions)

- [ ] Go to YouTube tab
- [ ] Enter a news video without captions
- [ ] Click "Analyze YouTube URL"
- [ ] Monitor logs in backend terminal:
  - [ ] `[YouTube] Starting analysis`
  - [ ] `[YouTube] Using SLOW PATH`
  - [ ] `[Job UUID] Starting video download...`
  - [ ] Status messages appear in frontend UI
  - [ ] `[Job UUID] PROCESSING COMPLETE - SUCCESS`
- [ ] Final result displays (should take 2-5 minutes)
- [ ] Shows Fake/Real prediction with confidence

### Test 5: Progress Messages

- [ ] While processing, watch frontend status message
- [ ] Should see updates like:
  - "Processing: Downloading video..."
  - "Processing: Extracting video frames..."
  - "Processing: OCR Progress: X/Y frames"
  - "Processing: Predicting fake/real..."
- [ ] At least 3-4 different status messages appear

### Test 6: Error Handling

- [ ] Invalid YouTube URL:
  - [ ] Enter "not-a-url"
  - [ ] Should show error immediately
- [ ] Private/Age-restricted video:
  - [ ] Should show error about authentication
- [ ] Very long video (test with search):
  - [ ] Should either process (might take 10+ min) or timeout gracefully
  - [ ] Should show job ID if timeout

### Test 7: Concurrent Jobs

- [ ] Submit multiple YouTube URLs simultaneously
- [ ] Each should show unique job ID
- [ ] Frontend logs should show different poll attempts
- [ ] Results should display as each job completes

### Test 8: Browser DevTools Debugging

- [ ] Open DevTools (F12)
- [ ] Go to Console tab
- [ ] Submit YouTube analysis
- [ ] Should see:
  - `[YouTube] Sending request to backend...`
  - `[YouTube] Response: {success: true, ...}`
  - `[YouTube] Poll attempt 1: Status check...`
  - etc.
- [ ] No JavaScript errors

### Test 9: Backend Logs Check

- [ ] Run backend in terminal
- [ ] Submit YouTube analysis
- [ ] Check for patterns:
  - `[YouTube] Starting analysis for URL`
  - `[YouTube] Video: "Title..." (Duration: XXXs)`
  - Either `[YouTube] Using FAST PATH` or `[YouTube] Using SLOW PATH`
  - Job-specific logs with `[Job UUID]` prefix
  - Final `PROCESSING COMPLETE - SUCCESS` or error

### Test 10: Job Status Query

- [ ] Get a job ID from any YouTube analysis
- [ ] Query manually:
  ```bash
  curl http://127.0.0.1:5000/api/v1/job/JOB_ID_HERE | json_pp
  ```
- [ ] Response should include:
  - [ ] `status` field (queued, downloading, finished, error, etc.)
  - [ ] `progress_message` field (when available)
  - [ ] `result` field (when finished)
  - [ ] `error` field (when status is error)

---

## Performance Verification

| Operation                | Expected Time | Actual Time |
| ------------------------ | ------------- | ----------- |
| Text prediction          | 1-3 seconds   | **\_**      |
| Fast path (captions)     | 5-10 seconds  | **\_**      |
| Slow path (full video)   | 2-5 minutes   | **\_**      |
| Job status query         | <1 second     | **\_**      |
| Multiple concurrent jobs | Additive      | **\_**      |

---

## Code Quality Checks

### Python Backend

```bash
# Check for syntax errors (run in project root)
python -m py_compile backend/app.py

# Expected: No output (clean)
```

### JavaScript Frontend

```bash
# Build should complete without errors
cd frontend
npm run build

# Expected: No critical errors
```

### Error Handling

- [ ] All endpoints return proper JSON responses
- [ ] Error responses include `success: false` and `error` message
- [ ] Success responses include `success: true` and `data`
- [ ] HTTP status codes are correct (200, 400, 404, 500)

### Logging

- [ ] Backend logs have `[YouTube]` or `[Job ID]` prefixes
- [ ] Frontend logs appear in browser console
- [ ] No sensitive data logged (passwords, API keys, etc.)

---

## Thread Safety Verification

### Verify Lock Usage

```bash
# Check that ThreadSafeJobStore is used
grep -n "app.job_store.get\|app.job_store.set\|app.job_store.update" backend/app.py

# Should see multiple calls with no direct dictionary access
```

### Concurrent Job Handling

- [ ] Submit 3+ YouTube analyses simultaneously
- [ ] Each should get unique job ID
- [ ] No race conditions in logs (should be sequential or properly interlocked)
- [ ] All jobs complete independently

---

## Cleanup Verification

### Temporary File Cleanup

- [ ] After YouTube analysis completes, check temp directories:

  ```bash
  # On Windows
  dir %TEMP% | find "ytdl"

  # On Linux/Mac
  ls -la /tmp | grep ytdl
  ```

- [ ] Should have minimal or no leftover files
- [ ] No accumulation of temp files over multiple runs

### Memory Cleanup

- [ ] Monitor backend process memory
- [ ] After 5-10 YouTube analyses, memory should not continuously grow
- [ ] Job store should clean up finished jobs (or implement periodic cleanup)

---

## Production Readiness Checklist

### Architecture

- [ ] Thread-safe operations with proper locking
- [ ] Proper exception handling in all code paths
- [ ] No blocking operations in main thread
- [ ] Proper resource cleanup (files, connections)

### User Experience

- [ ] Clear progress messages during processing
- [ ] Meaningful error messages with actionable info
- [ ] Job IDs provided for long-running operations
- [ ] No infinite loading states
- [ ] Graceful degradation on errors

### Reliability

- [ ] No race conditions
- [ ] Timeout handling prevents infinite loops
- [ ] Proper HTTP status codes
- [ ] Consistent API responses
- [ ] Proper logging for debugging

### Performance

- [ ] Fast path works in <10 seconds
- [ ] Slow path handles 1+ hour videos
- [ ] Multiple concurrent jobs handled
- [ ] No memory leaks
- [ ] No unresponsive states

### Security

- [ ] No sensitive data in logs
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] Error messages don't expose internals
- [ ] Proper cleanup of temporary files

---

## Common Issues & Resolution

| Issue                          | Resolution                           |
| ------------------------------ | ------------------------------------ |
| "yt-dlp is required"           | Run `pip install yt-dlp`             |
| "FFmpeg not found"             | Install FFmpeg (apt/brew/choco)      |
| Job stuck forever              | Check backend logs, restart          |
| Frontend blank page            | Check CORS, network tab, console     |
| Timeout after 3 minutes        | Job still running, try shorter video |
| Permission denied on temp file | Check OS temp folder permissions     |
| Port 5000 already in use       | Change backend port in config        |
| CORS errors                    | Check config.CORS_ORIGINS setting    |

---

## Sign-Off

- [ ] All tests passed
- [ ] No errors in logs
- [ ] Code review completed
- [ ] Performance acceptable
- [ ] Ready for production
- [ ] Documentation complete

**Deployer**: ******\_******  
**Date**: ******\_******  
**Status**: ✅ READY / ⚠️ ISSUES FOUND

---

## Notes

```
(Space for deployment notes and issues)




```

---

**Document**: Deployment & Verification Checklist  
**Version**: 1.0  
**Status**: ✅ PRODUCTION READY  
**Last Updated**: 2024
