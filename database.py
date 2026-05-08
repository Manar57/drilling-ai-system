import sqlite3
import hashlib
from datetime import datetime

DB_PATH = r"C:\Users\Manar\Desktop\sPro\classification.db"

def init_db():
    """Initialize database with all tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Classification history table (linked to user)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            image_name TEXT,
            image_data TEXT,
            lithology TEXT,
            confidence REAL,
            color TEXT,
            grain_size TEXT,
            angularity TEXT,
            depth REAL,
            wob REAL,
            rop REAL,
            response_time REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Batch jobs table (linked to user)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            total_images INTEGER,
            successful INTEGER,
            failed INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, email, password):
    """Add new user to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hash_password(password))
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def save_classification(user_id, username, data):
    """Save classification result to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO classifications (
            user_id, username, image_name, image_data, lithology, confidence,
            color, grain_size, angularity, depth, wob, rop, response_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, username, data.get('image_name'), data.get('image_data'),
        data['lithology'], data['confidence'],
        data['color'], data['grain_size'], data['angularity'],
        data.get('depth'), data.get('wob'), data.get('rop'), 
        data.get('response_time')
    ))
    conn.commit()
    conn.close()

def save_batch_job(user_id, username, total, successful, failed):
    """Save batch job record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO batch_jobs (user_id, username, total_images, successful, failed)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, total, successful, failed))
    conn.commit()
    conn.close()

def get_user_history(user_id, limit=50):
    """Get user's classification history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT image_name, lithology, confidence, timestamp 
        FROM classifications 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))
    history = cursor.fetchall()
    conn.close()
    return history

def get_all_user_data(user_id):
    """Get all classifications for a user (for export)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT image_name, lithology, confidence, color, grain_size, 
               angularity, depth, wob, rop, response_time, timestamp
        FROM classifications 
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def get_user_stats(user_id):
    """Get user statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total classifications
    cursor.execute("SELECT COUNT(*) FROM classifications WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    
    # Most common lithology
    cursor.execute('''
        SELECT lithology, COUNT(*) as count 
        FROM classifications 
        WHERE user_id = ? 
        GROUP BY lithology 
        ORDER BY count DESC 
        LIMIT 1
    ''', (user_id,))
    most_common = cursor.fetchone()
    
    # Average confidence
    cursor.execute("SELECT AVG(confidence) FROM classifications WHERE user_id = ?", (user_id,))
    avg_conf = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total': total,
        'most_common': most_common[0] if most_common else 'None',
        'avg_confidence': round(avg_conf, 2) if avg_conf else 0
    }

if __name__ == '__main__':
    init_db()
    print("✅ Database ready. Users can register through the web interface.")