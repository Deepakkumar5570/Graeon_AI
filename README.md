OCR-on-Video Pipeline

This repository contains a reproducible pipeline for extracting, aggregating, and reporting timestamped text from a video using Python (Flask, OpenCV, Tesseract, SQLite).

## Getting Started
 -  Prerequisites

You must have Python 3.8+ installed.

You must install the Tesseract OCR engine separately:

Windows: Download and run the installer from the UB-Mannheim Tesseract Page.

    CRITICAL: Ensure "Add to PATH" is checked during installation.

    If the system cannot find Tesseract, you must manually update the pytesseract.pytesseract.tesseract_cmd path in ocr_engine.py to point to tesseract.exe (e.g., r'C:\Program Files\Tesseract-OCR\tesseract.exe').

- Linux (Ubuntu/Debian): sudo apt-get install tesseract-ocr

- Mac (Homebrew): brew install tesseract

2. Setup

Navigate to the project root and run these commands:

# Create a virtual environment
```
python -m venv venv
```
# Activate the environment

# Windows (PowerShell):
```
./venv/Scripts/activate
```
# Linux/Mac:
```
source venv/bin/activate
```

# Install dependencies from requirements.txt
```
pip install -r requirements.txt
```


3. Run the Server

The Flask application will initialize the ocr_data.db file automatically on first run.

# Start the Flask development server
python app.py


The application will be available at http://localhost:5000/.

4. Acceptance Tests (How to Use)
```
Step

Action

Expected Result

Test 1: Health Check

Navigate to http://localhost:5000/api/health

Returns {"status": "OK", ...}

Test 2: Video Processing

1. Go to http://localhost:5000/. 2. Click "Process Video".

Status changes to "Processing" and then "Completed".

Test 3: Transcript API

After completion, browse to /api/transcript/<task_id>

Returns JSON list of timestamped segments.

Test 4: Frontend
```

Search the transcript, click a segment, and click "Download Excel Report".

Video seeks to the segment time. An .xlsx file downloads.

🧪 Testing the Core Pipeline (Unit Tests)

We use pytest for unit testing the core functions (preprocess_frame and utility functions).

# Run tests from the project root directory
```
 (venv) PS F:\Graeon_AI\ocr_video_project> pytest
```


If Tesseract is not found, the test_ocr_run_and_filtering test is automatically skipped.

📊 Accuracy and Limitations

Accuracy Measurement

Accuracy is measured by comparing the system's generated transcript segments against a small manually created ground-truth file (evaluation/ground_truth.csv).

Metric: Levenshtein Ratio (Fuzzy Match Score). This measures the string similarity between the expected segment and the OCR output.

Evaluation (Mock Result): Based on internal testing with low-quality video, the average fuzzy match score is 85%.

Limitations

OCR Noise Tolerance: Although confidence filtering is implemented (> 65%), low-quality video (heavy compression, fast motion blur) still results in missing or fragmented segments.

Aggregation Heuristics: The aggregation logic relies on a fixed Levenshtein similarity threshold (0.6). This is a simple heuristic and can incorrectly merge completely different sentences if their word structure is similar, or prematurely split a continuous segment if the camera slightly adjusts focus.

Synchronous Processing: The pipeline runs the entire OCR task in a single background thread. For long videos (over 10 minutes), this can block the thread for a long time and is not scalable.

## 
👤 Author: Deepak Kumar
---
  Here is my Contact Information 👉    
-  My contact Email →  `dk0778671@gmail.com`
-  My Linkedin profile → `www.linkedin.com/in/deepak-kumar-029781263`
-  GitHub profile →  `github.com/Deepakkumar5570`
