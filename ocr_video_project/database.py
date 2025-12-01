import sqlite3
import os

DB_NAME = "ocr_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            filename TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Raw Frames Table (Granular Data)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            frame_number INTEGER,
            timestamp_ms INTEGER,
            ocr_text TEXT,
            confidence REAL,
            FOREIGN KEY(task_id) REFERENCES tasks(task_id)
        )
    ''')

    # 3. Aggregated Segments Table (Clean Transcript)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            start_ts INTEGER,
            end_ts INTEGER,
            text TEXT,
            confidence REAL,
            FOREIGN KEY(task_id) REFERENCES tasks(task_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()