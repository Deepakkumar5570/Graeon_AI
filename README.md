# OCR-on-Video Transcript Tool

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

## Repo Structure (important files)

- `app.py` : Flask application, routes, upload handling, status polling, report export.
- `ocr_engine.py` : Video processing pipeline: preprocessing, OCR per frame, aggregation logic.
- `database.py` : SQLite helper and schema initialization (`tasks`, `frames`, `segments`).
- `templates/index.html` : Frontend UI (upload, player, transcript panel, overlay).
- `uploads/` : Saved uploaded video files.
- `output/` : Generated Excel reports.
- `requirements.txt` : Python dependencies (ensure to validate contents). 
- `test_tesseract.py` and `tests/` : Small tests and examples for preprocessing & Levenshtein checks.

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
- Required Python packages (typical):
  - `flask`
  - `opencv-python` (cv2)
  - `pytesseract`
  - `pandas`
  - `openpyxl`
  - `python-Levenshtein`
  - `pytest` (for tests)

Install dependencies (create a virtualenv first). On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `requirements.txt` is missing/partial, install manually:

```powershell
pip install flask opencv-python pytesseract pandas openpyxl python-Levenshtein pytest
```

### Tesseract OCR (external dependency)

This project uses Tesseract as an external executable. On Windows:

1. Download & install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki or https://github.com/tesseract-ocr/tesseract
2. Typical path on Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3. Set the path in `ocr_engine.py` (already present):

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

4. Verify installation:

```powershell
python test_tesseract.py
# or
tesseract --version
```

## Running Locally

Start the Flask app (development mode):

```powershell
python app.py
```

Then open `http://127.0.0.1:5000/` in your browser. Upload a video, and the UI will start processing and poll for task status.

Notes:
- Uploaded files are saved to `uploads/` as `<task_id>_<filename>`.
- Generated Excel reports are saved to `output/report_<task_id>.xlsx` and returned by the `send_file` response.

## Tests

Run unit tests with `pytest` from repo root:

```powershell
pytest -q
```

Some tests (e.g., OCR runtime) may be skipped if Tesseract is not available. The `test_tesseract.py` file can be used to validate Tesseract path.

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


