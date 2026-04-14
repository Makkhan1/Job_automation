import sqlite3
from datetime import datetime

DB_PATH = "pipeline.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create the single table needed for the dashboard
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT, -- 'incoming' or 'outgoing'
            source TEXT,    -- 'Channel', 'Group', 'Contact'
            platform TEXT,  -- 'telegram', 'whatsapp'
            name TEXT,
            preview TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_message(direction: str, source: str, platform: str, name: str, full_text: str):
    # Truncate text for the dashboard preview
    preview = full_text[:80] + "..." if len(full_text) > 80 else full_text
    
    # Force platform to lowercase ('telegram', 'whatsapp') so the FontAwesome icons work
    platform = platform.lower()
    
    # Grab exact local time so the dashboard shows the right hour
    local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (direction, source, platform, name, preview, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (direction, source, platform, name, preview, local_time))
    conn.commit()
    conn.close()

def get_full_dashboard_data():
    """Fetches real metrics and recent messages to feed the frontend JS."""
    conn = sqlite3.connect(DB_PATH)
    
    # This magic line tells SQLite to return rows as dictionaries instead of plain lists!
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # --- 1. Get Metrics ---
    cursor.execute("SELECT COUNT(*) FROM messages WHERE direction = 'incoming'")
    received = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages WHERE direction = 'outgoing'")
    processed = cursor.fetchone()[0]
    
    # --- 2. Get Recent Incoming Messages (Limit to 5) ---
    cursor.execute("SELECT source, platform, name, preview, timestamp FROM messages WHERE direction = 'incoming' ORDER BY timestamp DESC LIMIT 5")
    incoming_rows = cursor.fetchall()
    
    incoming = []
    for row in incoming_rows:
        # Convert "2026-04-02 14:30:00" into "02:30 PM"
        try:
            dt_obj = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            friendly_time = dt_obj.strftime('%I:%M %p')
        except:
            friendly_time = "Just now"

        incoming.append({
            "source": row['source'],
            "platform": row['platform'],
            "name": row['name'],
            "time": friendly_time,
            "preview": row['preview']
        })
        
    # --- 3. Get Recent Outgoing Messages (Limit to 5) ---
    cursor.execute("SELECT name as recipient, preview, timestamp FROM messages WHERE direction = 'outgoing' ORDER BY timestamp DESC LIMIT 5")
    outgoing_rows = cursor.fetchall()
    
    outgoing = []
    for row in outgoing_rows:
        try:
            dt_obj = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            friendly_time = dt_obj.strftime('%I:%M %p')
        except:
            friendly_time = "Just now"

        outgoing.append({
            "recipient": row['recipient'],
            "time": friendly_time,
            "preview": row['preview']
        })

    conn.close()
    
    # --- 4. Package it perfectly for the JS Frontend ---
    return {
        "metrics": {
            "received": received,
            "processed": processed,
            "ignored": 0, # Hardcoded until you build a filter logic
            "errors": 0   # Hardcoded until error catching is added
        },
        # We will pass a simple dynamic array for the chart to make it move
        "chartData": [0, max(0, received-5), received, max(0, processed-3), processed, received + 2, processed + 5],
        "incoming": incoming,
        "outgoing": outgoing
    }

def clear_all_data():
    """Utility function to clear the database (for testing/demo purposes)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()