import cv2
import pytesseract
import os
import sqlite3
from database import get_db_connection
from Levenshtein import ratio

# CONFIGURATION
# Point this to your tesseract executable if on Windows, e.g.:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_frame(frame):
    """
    Grayscale -> Resize -> Thresholding for better OCR
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Resize to specific width, keeping aspect ratio (optional, speeds up OCR)
    # height, width = gray.shape
    # r = 1000.0 / width
    # dim = (1000, int(height * r))
    # resized = cv2.resize(gray, dim, interpolation=cv2.INTER_AREA)
    
    # Simple binary thresholding
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def process_video(task_id, file_path, frame_skip=30):
    """
    frame_skip: Process 1 frame every 'frame_skip' frames. 
    If video is 30fps, frame_skip=30 means 1 FPS.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update status
    cursor.execute("UPDATE tasks SET status = 'processing' WHERE task_id = ?", (task_id,))
    conn.commit()

    cap = cv2.VideoCapture(file_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: fps = 30 # fallback
    
    frame_count = 0
    raw_results = []

    print(f"Starting processing for {task_id}...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Only process every Nth frame
        if frame_count % frame_skip == 0:
            timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            
            # 1. Preprocess
            processed_img = preprocess_frame(frame)
            
            # 2. OCR
            # psm 6 is good for block of text, psm 11 for sparse text
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT, config='--psm 6')
            
            # Extract high confidence text
            text_lines = []
            conf_sum = 0
            conf_count = 0
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 40: # Confidence threshold
                    txt = data['text'][i].strip()
                    if len(txt) > 1:
                        text_lines.append(txt)
                        conf_sum += int(data['conf'][i])
                        conf_count += 1
            
            full_text = " ".join(text_lines)
            avg_conf = (conf_sum / conf_count) if conf_count > 0 else 0

            if full_text:
                # Store Raw Frame Data
                cursor.execute(
                    "INSERT INTO frames (task_id, frame_number, timestamp_ms, ocr_text, confidence) VALUES (?, ?, ?, ?, ?)",
                    (task_id, frame_count, timestamp_ms, full_text, avg_conf)
                )
                raw_results.append({
                    'ts': timestamp_ms,
                    'text': full_text,
                    'conf': avg_conf
                })
        
        frame_count += 1

    cap.release()
    conn.commit()
    
    # 3. Aggregation Logic (Deduplication)
    aggregate_segments(task_id, raw_results, cursor)
    
    # Finish
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()
    print(f"Processing complete for {task_id}")

def aggregate_segments(task_id, raw_data, cursor):
    """
    Merges consecutive frames with similar text into segments.
    """
    if not raw_data:
        return

    segments = []
    current_seg = {
        'start': raw_data[0]['ts'],
        'end': raw_data[0]['ts'],
        'text': raw_data[0]['text'],
        'conf_accum': raw_data[0]['conf'],
        'count': 1
    }

    for i in range(1, len(raw_data)):
        frame = raw_data[i]
        
        # Calculate similarity (Levenshtein Ratio)
        sim = ratio(current_seg['text'], frame['text'])
        
        if sim > 0.6: # If 60% similar, consider it the same sentence
            # Extend segment
            current_seg['end'] = frame['ts']
            # Optionally update text to the longer one or average them
            if len(frame['text']) > len(current_seg['text']):
                current_seg['text'] = frame['text']
            current_seg['conf_accum'] += frame['conf']
            current_seg['count'] += 1
        else:
            # Save current segment and start new
            avg_conf = current_seg['conf_accum'] / current_seg['count']
            segments.append((current_seg['start'], current_seg['end'], current_seg['text'], avg_conf))
            
            # Reset
            current_seg = {
                'start': frame['ts'],
                'end': frame['ts'],
                'text': frame['text'],
                'conf_accum': frame['conf'],
                'count': 1
            }
            
    # Append last segment
    avg_conf = current_seg['conf_accum'] / current_seg['count']
    segments.append((current_seg['start'], current_seg['end'], current_seg['text'], avg_conf))

    # Bulk Insert
    for s in segments:
        cursor.execute(
            "INSERT INTO segments (task_id, start_ts, end_ts, text, confidence) VALUES (?, ?, ?, ?, ?)",
            (task_id, s[0], s[1], s[2], s[3])
        )