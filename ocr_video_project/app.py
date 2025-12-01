import os
import uuid
import threading
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from database import init_db, get_db_connection
from ocr_engine import process_video

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize DB on start
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    task_id = str(uuid.uuid4())
    filename = file.filename
    save_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
    file.save(save_path)
    
    conn = get_db_connection()
    conn.execute("INSERT INTO tasks (task_id, filename, status) VALUES (?, ?, ?)", 
                 (task_id, filename, 'pending'))
    conn.commit()
    conn.close()

    # Run asynchronously using a Thread
    thread = threading.Thread(target=process_video, args=(task_id, save_path))
    thread.start()
    
    return jsonify({"task_id": task_id, "status": "processing"}), 202

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    conn = get_db_connection()
    task = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    conn.close()
    if task:
        return jsonify({"status": task['status']})
    return jsonify({"error": "Task not found"}), 404

@app.route('/api/transcript/<task_id>', methods=['GET'])
def get_transcript(task_id):
    query = request.args.get('q', '').lower()
    conn = get_db_connection()
    
    if query:
        # Simple search capability
        sql = "SELECT * FROM segments WHERE task_id = ? AND lower(text) LIKE ?"
        rows = conn.execute(sql, (task_id, f'%{query}%')).fetchall()
    else:
        rows = conn.execute("SELECT * FROM segments WHERE task_id = ?", (task_id,)).fetchall()
    
    conn.close()
    
    results = [dict(row) for row in rows]
    return jsonify({"segments": results})

@app.route('/api/report/excel', methods=['GET'])
def download_excel():
    task_id = request.args.get('task_id')
    conn = get_db_connection()
    
    # Fetch Data
    segments = pd.read_sql_query("SELECT start_ts, end_ts, text, confidence FROM segments WHERE task_id = ?", conn, params=(task_id,))
    task_info = pd.read_sql_query("SELECT * FROM tasks WHERE task_id = ?", conn, params=(task_id,))
    conn.close()

    if segments.empty:
        return jsonify({"error": "No data found"}), 404

    # Generate Excel
    filename = f"report_{task_id}.xlsx"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        segments.to_excel(writer, sheet_name='Transcript', index=False)
        task_info.to_excel(writer, sheet_name='Summary', index=False)
        
    return send_file(filepath, as_attachment=True)

# Add route to serve uploaded video for the player
@app.route('/uploads/<filename>')
def serve_video(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

if __name__ == '__main__':
    app.run(debug=True, port=5000)