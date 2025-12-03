<!-- <p align="center">
  <img src="YOUR_BANNER_IMAGE_URL_HERE" width="100%" alt="Graeon.ai — OCR on Video">
</p> -->

<h1 align="center">🎥 Graeon.ai — OCR on Video</h1>
<h3 align="center">Intelligent Video Text Extraction using Computer Vision + Tesseract OCR</h3>

<p align="center">
<img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge">
<img src="https://img.shields.io/badge/Flask-Framework-black?style=for-the-badge">
<img src="https://img.shields.io/badge/Tesseract-OCR-green?style=for-the-badge">
<img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-red?style=for-the-badge"><br>
<img src="https://img.shields.io/github/stars/Deepakkumar5570/Graeon_AI?style=for-the-badge">
<img src="https://img.shields.io/github/issues/Deepakkumar5570/Graeon_AI?style=for-the-badge">
<img src="https://img.shields.io/github/license/Deepakkumar5570/Graeon_AI?style=for-the-badge">
</p>


## Project Summary

This repository contains a Flask-based application that extracts text from video files using Tesseract OCR and produces a timestamped transcript. It stores processing metadata and results in a local SQLite database, provides a web UI for uploading and reviewing transcripts with a synchronized video player overlay, and exposes HTTP APIs for status, transcript retrieval (with search), and exporting reports to Excel.

This project is intended as a lightweight, local video OCR pipeline useful for captioning, indexing, and searching text that appears in video frames.

## Key Features

- **Video upload & processing**: Upload video files through the web UI (or API) and process them asynchronously.
- **Frame-level OCR**: Extract text from sampled frames using Tesseract via `pytesseract`.
- **Aggregation**: Merge consecutive frames with similar text into clean segments using Levenshtein similarity.
- **Searchable transcript**: Retrieve segments via API with a `q` search parameter (case-insensitive substring match).
- **Export**: Download a report as an Excel workbook (transcript + task summary).
- **Local DB**: All tasks, raw frame OCR outputs, and aggregated segments are stored in `sqlite3`.

### 🔧 Backend
- Video upload & background processing  
- Frame-wise OCR (Tesseract via `pytesseract`)  
- Grayscale, denoise, threshold preprocessing  
- Levenshtein similarity for segment merging  
- SQLite database for persistence  
- Excel report generation  

### 🖥 Frontend
- Clean HTML UI  
- Video player + transcript sidebar  
- Searchable transcript  
- Auto polling for task status  
- Excel download button  



---

# 🧭 Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [How It Works](#how-it-works)
- [Configuration Options](#configuration-options)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Future Improvements](#future-improvements)
- [Developer Guide](#developer-guide)

---

## Architecture
```
┌────────────────────────────┐
│        Frontend UI         │
│     (templates/index.html) │
└──────────────┬─────────────┘
               │ AJAX Requests
               ▼
┌────────────────────────────┐
│         Flask API          │
│         app.py             │
└──────────────┬─────────────┘
               │
               ├────────► SQLite (tasks, frames, segments)
               │
               ├────────► Tesseract OCR Engine
               │
               └────────► File Storage (uploads/, output/)

```

## Project Structure
```
Graeon_AI/
├── app.py               # Main Flask application
├── ocr_engine.py        # Video processing + OCR pipeline
├── database.py          # Database schema + helper functions
├── requirements.txt     # Backend dependencies
├── templates/
│   └── index.html       # Web UI
├── uploads/             # Uploaded videos
├── output/              # Excel reports
├── test_tesseract.py    # Tesseract installation tester
└── tests/               # Unit tests

```
## How It Works — Processing Pipeline (step-by-step)

1. User uploads a video via the web UI or `POST /api/process`.
2. `app.py` saves the file to `uploads/`, creates a DB `task` row (status: `pending`), and starts a background `threading.Thread` running `process_video(task_id, path)` from `ocr_engine.py`.
3. `process_video` updates the task status to `processing`, opens the video with OpenCV, and samples frames at a cadence determined by `frame_skip` (default: 30).
   - For each sampled frame:
     - `preprocess_frame(frame)` converts to grayscale and applies a binary threshold to improve OCR.
     - `pytesseract.image_to_data` is used to extract text and per-word confidence scores.
     - High-confidence words (confidence > 40) are concatenated and stored as a row in the `frames` table with the timestamp (ms) and average confidence.
4. After the video is scanned, `aggregate_segments` groups consecutive frames with similar text into segments using a Levenshtein ratio threshold (sim > 0.6 means same segment). The aggregated results are inserted into `segments` with `start_ts`, `end_ts`, `text`, and average confidence.
5. `process_video` marks the task `completed` once finished. The frontend polls `GET /api/status/<task_id>` to update UI state.
6. Transcript segments are served by `GET /api/transcript/<task_id>?q=...` (optional search), and a synchronized overlay/highlight is shown in the UI while the user plays the saved video.
7. Reports are generated to Excel via `GET /api/report/excel?task_id=<id>` and saved in `output/`.

## Database schema (SQLite)

- `tasks(task_id TEXT PRIMARY KEY, filename TEXT, status TEXT, created_at TIMESTAMP)`
- `frames(id INTEGER PK, task_id TEXT, frame_number INTEGER, timestamp_ms INTEGER, ocr_text TEXT, confidence REAL)`
- `segments(id INTEGER PK, task_id TEXT, start_ts INTEGER, end_ts INTEGER, text TEXT, confidence REAL)`

These are created by `database.py` when the application starts.

## API Endpoints (quick reference)

- `POST /api/process` — Upload a `multipart/form-data` video with name `file`. Returns `{task_id, status}`. Status `202`.
- `GET /api/status/<task_id>` — Returns `{status}` (e.g., `pending`, `processing`, `completed`).
- `GET /api/transcript/<task_id>?q=<query>` — Returns `{segments: [...]}`. If `q` present, performs a case-insensitive search over `text`.
- `GET /api/report/excel?task_id=<task_id>` — Generates and returns an Excel workbook containing `Transcript` and `Summary` sheets.
- `GET /uploads/<filename>` — Serve the uploaded video to the player.

Example `curl` upload (PowerShell):

```powershell
curl -F "file=@C:\path\to\video.mp4" http://127.0.0.1:5000/api/process
```

Example download Excel (PowerShell):

```powershell
Invoke-WebRequest "http://127.0.0.1:5000/api/report/excel?task_id=<task-id>" -OutFile report.xlsx
```

## Requirements & Setup

- Recommended Python: `3.9` — `3.11` (verify compatibility)
- Tesseract OCR installed
- Pip + virtual environment recommended
- Required Python packages (typical):
  - `flask`
  - `opencv-python` (cv2)
  - `pytesseract`
  - `pandas`
  - `openpyxl`
  - `python-Levenshtein`
  - `pytest` (for tests)
## Installation & Setup
- Install dependencies (create a virtualenv first). On Windows PowerShell:
 ## 

### Tesseract OCR (external dependency)

This project uses Tesseract as an external executable. On Windows:

1. Download & install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki or https://github.com/tesseract-ocr/tesseract
2. Typical path on Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3. Set the path in `ocr_engine.py` (already present):
- For macOS
  ```
  brew install tesseract
  ```
- For Linux
   ```
  sudo apt update
  sudo apt install tesseract-ocr
  ```
- Verify
  ```
  tesseract --version
  ```
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

4. Verify installation:

   ```powershell
     tesseract --version
   ```


- Backend Setup
  ```
  git clone https://github.com/Deepakkumar5570/Graeon_AI
  cd Graeon_AI/ocr_video_project
- Create Virtual env.
   ```
   python -m venv .venv
- Activate(Windows):
   ```
    venv\Scripts\activate
- For macOS/Linux:
   ```
   source .venv/bin/activate
- Install dependencies:
    ```
     pip install -r requirements.txt
If `requirements.txt` is missing/partial, install manually:

- powershell
  ```
  pip install flask opencv-python pytesseract pandas openpyxl python-Levenshtein pytest

## Tests
Run unit tests with `pytest` from repo root:
    ```
       pytest
    ```

   

Some tests (e.g., OCR runtime) may be skipped if Tesseract is not available. The `test_tesseract.py` file can be used to validate Tesseract path.
- Run Tesseract test:
   ```
   python test_tesseract.py
## Frontend Setup
 - No separate setup.
 - UI is rendered directly through Flask.
## Running the Application
- Start the Server
   ```
    python app.py
 - Your app will start at:
   ```
   👉 http://127.0.0.1:5000
   ```
Then open `http://127.0.0.1:5000/` in your browser. Upload a video, and the UI will start processing and poll for task status.

Notes:


- Using the App (Uploaded files are saved to `uploads/` as `<task_id>_<filename>`.)
- Upload a video
- Wait for processing
- Watch video + transcript
- Search inside transcript
- Download Excel report  (Generated Excel reports are saved to `output/report_<task_id>.xlsx` and returned by the   `send_file` response.)

## API Documentation
- Base URL 
   ```
   http://127.0.0.1:5000/api
- Health Check
  ```
  GET /api/health
- Upload Video
   ```
   POST /api/process
  Content-Type: multipart/form-data
  file=@video.mp4
- Response
   ```
    {
  "task_id": "UUID",
  "status": "processing"
  }
- Task Status
   ```
    GET /api/status/<task_id>
- Transcript
   ```
    GET /api/transcript/<task_id>?q=search
- Download Excel
   ```
    GET /api/report/excel?task_id=<task_id>

## Database Schema
### 🗄 tasks Table

| Column      | Type      | Description                     |
|-------------|-----------|---------------------------------|
| task_id     | TEXT      | Primary Key (UUID)              |
| filename    | TEXT      | Original filename               |
| status      | TEXT      | processing / completed / failed |
| created_at  | TIMESTAMP | Start time                      |
| updated_at  | TIMESTAMP | Last update time                |

   
### 🗄 tasks Table

| Column      | Type      | Description                     |
|-------------|-----------|---------------------------------|
| task_id     | TEXT      | Primary Key (UUID)              |
| filename    | TEXT      | Original filename               |
| status      | TEXT      | processing / completed / failed |
| created_at  | TIMESTAMP | Start time                      |
| updated_at  | TIMESTAMP | Last update time                |


 ### 🗄 frames Table

| Column        | Type      | Description                               |
|---------------|-----------|-------------------------------------------|
| id            | INTEGER   | Primary Key (auto-increment)              |
| task_id       | TEXT      | Foreign Key → tasks.task_id               |
| frame_number  | INTEGER   | Frame index                               |
| timestamp_ms  | INTEGER   | Timestamp of frame in milliseconds        |
| ocr_text      | TEXT      | Full OCR output from this frame           |
| ocr_snippet   | TEXT      | First 200 chars (optional summary)        |
| confidence    | REAL      | OCR confidence score (0.0 – 1.0)          |
| bbox_json     | TEXT      | Bounding boxes in JSON format             |
| processed_at  | TIMESTAMP | When this frame OCR processing finished   |


## How It Works
### Frame Extraction
- Extract 1 frame per second (configurable).
### Preprocessing
- Resize
- Grayscale
- Denoise
- Threshold


## ⚙️Configuration Options

| Option                 | Description                           |
|------------------------|---------------------------------------|
| `frame_skip`           | Controls how many frames to skip (affects speed vs accuracy) |
| `tesseract_cmd`        | Absolute system path to the Tesseract OCR executable |
| `similarity_threshold` | Levenshtein similarity required to merge frames into segments |
| `min_confidence`       | Minimum OCR confidence required to include a word |




## Troubleshooting & Common Issues

- If you see empty transcripts:
  - Confirm Tesseract is installed and the path in `ocr_engine.py` is correct.
  - Increase frame sampling (reduce `frame_skip`) or improve preprocessing (resize, adaptive thresholding).
- If OpenCV fails to open a video:
  - Confirm the video is a supported format and codecs are installed.
- If confidence values are low or noisy:
  - Tune OCR `config` (PSM mode) and change the confidence threshold in `ocr_engine.py`.
- If DB file locked or concurrency issues:
  - Ensure commits are performed and connections closed; consider serializing writes or using a queue for high concurrency.

## Security & Privacy Considerations

- This app stores uploaded video files and extracted text locally. Avoid running on a public network without authentication.
- If processing private videos, ensure `uploads/` and `ocr_data.db` are stored securely (or configured to use a secure storage backend).

## Suggested Improvements / Next Steps

- Add authenticated access and user accounts.
- Add progress reporting with more granular status (frames processed / total frames).
- Replace background thread with a job queue (Redis + RQ, Celery) for reliability and scaling.
- Add more robust OCR preprocessing (dynamically detect text regions, morphological filters, adaptive threshold, denoising).
- Add concurrency-safe DB access or move to a server-based DB for multi-worker setups.
- Add confidence-aware word-level timestamps for subtitle generation (SRT/VTT export).

## Where to Start for a New Developer

1. Install Python and Tesseract following instructions above.
2. Create & activate a virtual environment and install requirements.
3. Run `python app.py` and visit the UI.
4. Open `ocr_engine.py` and `app.py` to trace the end-to-end flow.
5. Run `pytest` to validate small unit tests.

---


